/**
 * cashier.js
 * Specialized for the Cashier dashboard.
 * Handles Orders and Customers.
 */

const ADMIN_DATA = {
  orders: [],
  tables: [], // Physical tables
  shippers: [], // For order assignment if needed
  revenue: [
    { day: "Mon", amount: 0 },
    { day: "Tue", amount: 0 },
    { day: "Wed", amount: 0 },
    { day: "Thu", amount: 0 },
    { day: "Fri", amount: 0 },
    { day: "Sat", amount: 0 },
    { day: "Sun", amount: 0 },
  ],
};

const SESSION_USER_KEY = "tay_coffee_current_user";
const SESSION_STORAGE_KEY = "tay_coffee_current_user_email";

const STATUS_MAP = {
  pending: { label: "Chờ xử lý", cls: "sbadge-warning" },
  preparing: { label: "Đang pha chế", cls: "sbadge-warning" },
  served: { label: "Đã phục vụ", cls: "sbadge-info" },
  completed: { label: "Hoàn tất", cls: "sbadge-success" },
  cancelled: { label: "Đã hủy", cls: "sbadge-danger" },
};

let editingUserId = null;
let editingUserRole = "customer";
const filterTimers = {};

function initContrastModeWatcher() {
  if (typeof window === "undefined") return;
  const contrastQueries = [
    window.matchMedia("(forced-colors: active)"),
    window.matchMedia("(prefers-contrast: more)"),
  ];
  const update = () => {
    const shouldForce = contrastQueries.some((mq) => mq && mq.matches);
    if (shouldForce) {
      document.body.classList.add("admin-contrast-mode");
    } else {
      document.body.classList.remove("admin-contrast-mode");
    }
  };
  contrastQueries.forEach((mq) => {
    if (!mq) return;
    mq.addEventListener("change", update);
  });
  update();
}

function getAdminApiBase() {
  const { protocol, host } = window.location;
  return `${protocol}//${host}/api`;
}

async function loadCashierDataFromAPI() {
  try {
    const [orders, tables] = await Promise.all([
      fetchItems("/orders"),
      fetchItems("/tables"),
    ]);

    const ordersByCustomer = {};
    ADMIN_DATA.orders = (orders || []).map((o) => {
      const dbId = Number(o.orderid);
      const customerId = Number(o.customerid) || null;
      if (customerId) {
        ordersByCustomer[customerId] = (ordersByCustomer[customerId] || 0) + 1;
      }
      return {
        id: `TC-${String(o.orderid).padStart(4, '0')}`,
        dbId,
        customerId,
        customer: o.customer_name || (customerId ? `Customer #${customerId}` : 'Customer'),
        items: o.items_summary || 'Xem chi tiết',
        subtotal: Number(o.subtotal || 0),
        discount: Number(o.discount || 0),
        get total() {
          return (this.subtotal) - this.discount;
        },
        tableNumber: o.tablenumber || o.table_id || '-',
        status: o.orderstatus || 'pending',
        date: o.orderdate ? new Date(o.orderdate).toLocaleString('vi-VN') : '-',
        notes: o.notes || '',
      };
    });

    ADMIN_DATA.tables = (tables || []).map((t) => ({
      id: t.tableid,
      number: t.tablenumber,
      capacity: t.capacity,
      status: t.status,
    }));

  } catch (err) {
    console.error("[Cashier] Failed to load data:", err);
    throw err;
  }
}

async function fetchItems(path) {
  const res = await fetch(`${getAdminApiBase()}${path}`);
  const data = await res.json();
  return Array.isArray(data.items) ? data.items : [];
}

async function fetchAdminUsers(role) {
  const url = `${getAdminApiBase()}/admin/users?role=${role}`;
  const res = await fetch(url);
  const data = await res.json();
  return Array.isArray(data.items) ? data.items : [];
}

function showPanel(panelId, navEl) {
  document.querySelectorAll(".a-panel").forEach((p) => p.classList.remove("active"));
  const target = document.getElementById(`panel-${panelId}`);
  if (target) target.classList.add("active");

  document.querySelectorAll(".a-nav-item").forEach((n) => n.classList.remove("active"));
  if (navEl) navEl.classList.add("active");
}

function renderOrders() {
  const tbody = document.getElementById("orders-body");
  if (!tbody) return;
  if (ADMIN_DATA.orders.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="table-empty">Không có đơn hàng nào</td></tr>';
    return;
  }

  tbody.innerHTML = ADMIN_DATA.orders.map((o) => {
    const s = STATUS_MAP[o.status] || { label: o.status, cls: "" };
    const statusOptions = Object.keys(STATUS_MAP)
      .map(k => `<option value="${k}" ${k === o.status ? "selected" : ""}>${STATUS_MAP[k].label}</option>`)
      .join("");
    
    const notesHtml = o.notes ? `<div style="font-size:11px;color:var(--gold);margin-top:6px;font-style:italic;opacity:0.8">
      <i class="fa-solid fa-comment-dots" style="margin-right:4px"></i>${o.notes}
    </div>` : '';

    return `<tr>
      <td style="font-weight:700;color:var(--white)">${o.id}</td>
      <td style="font-weight:600">${o.customer}</td>
      <td style="max-width:200px">
        <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${o.items}</div>
        ${notesHtml}
      </td>
      <td style="color:var(--gold);font-weight:700">${Number(o.total).toLocaleString('vi-VN')}₫</td>
      <td><span style="padding:4px 8px;background:rgba(255,255,255,0.05);border-radius:4px">${o.tableNumber}</span></td>
      <td>
        <span class="sbadge ${s.cls}">${s.label}</span>
        <select class="status-select" onchange="updateOrderStatus('${o.dbId}', this.value)">
          ${statusOptions}
        </select>
      </td>
      <td style="font-size:12px;opacity:0.6">${o.date}</td>
      <td>
        <button class="abtn abtn-view" onclick="openOrderDetails('${o.id}')">
            <i class="fa-solid fa-eye"></i> Chi tiết
        </button>
      </td>
    </tr>`;
  }).join("");
}

function renderTables() {
  const tbody = document.getElementById("tables-body");
  if (!tbody) return;
  tbody.innerHTML = ADMIN_DATA.tables.map((t) => {
    const isOccupied = t.status.toLowerCase() === 'occupied';
    const statusClass = isOccupied ? 'sbadge-danger' : 'sbadge-success';
    const statusLabel = isOccupied ? 'Có khách' : 'Trống';
    const statusIcon = isOccupied ? 'fa-user-clock' : 'fa-check-circle';
    
    return `
      <tr>
        <td style="font-weight:700;font-size:16px;color:var(--gold)">Bàn ${t.number}</td>
        <td>${t.capacity} người</td>
        <td>
            <span class="sbadge ${statusClass}">
                <i class="fa-solid ${statusIcon}" style="margin-right:6px"></i>${statusLabel}
            </span>
        </td>
        <td>
          <button class="abtn abtn-edit" onclick="updateTableStatus('${t.id}', '${isOccupied ? 'Empty' : 'Occupied'}')">
            <i class="fa-solid ${isOccupied ? 'fa-door-open' : 'fa-lock-open'}"></i>
            ${isOccupied ? 'Giải phóng' : 'Mở bàn'}
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

async function updateTableStatus(tableId, newStatus) {
  try {
    const res = await APIClient.updateTableStatus(tableId, newStatus);
    if (res.ok) {
      adminToast("Cập nhật trạng thái bàn thành công", "success");
      await loadCashierDataFromAPI();
      renderTables();
    } else {
      throw new Error(res.error || "Update failed");
    }
  } catch (err) {
    adminToast(err.message, "error");
  }
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    const res = await APIClient.updateOrderStatus(orderId, newStatus);
    if (res.ok) {
      adminToast("Cập nhật trạng thái thành công", "success");
      await loadCashierDataFromAPI();
      renderOrders();
    } else {
      throw new Error(res.error || "Update failed");
    }
  } catch (err) {
    adminToast(err.message, "error");
  }
}

function openOrderDetails(displayId) {
  const modal = document.getElementById("order-modal");
  const order = ADMIN_DATA.orders.find(o => o.id === displayId);
  if (!order || !modal) return;

  document.getElementById("order-detail-id").textContent = order.id;
  document.getElementById("order-detail-customer").textContent = order.customer;
  document.getElementById("order-detail-shipper").textContent = order.tableNumber;
  document.getElementById("order-detail-subtotal").textContent = `${Number(order.subtotal).toLocaleString('vi-VN')}₫`;
  document.getElementById("order-detail-total").textContent = `${Number(order.total).toLocaleString('vi-VN')}₫`;
  document.getElementById("order-detail-status").textContent = STATUS_MAP[order.status]?.label || order.status;
  document.getElementById("order-detail-date").textContent = order.date;
  document.getElementById("order-detail-items").textContent = order.items;
  document.getElementById("order-detail-notes").textContent = order.notes || '-';

  modal.classList.remove("hidden");
}

function closeOrderModal() {
  document.getElementById("order-modal").classList.add("hidden");
}

function adminToast(msg, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

document.addEventListener("DOMContentLoaded", async () => {
  initContrastModeWatcher();
  try {
    await loadCashierDataFromAPI();
    renderOrders();
    renderTables();
    
    // Polling
    setInterval(async () => {
      await loadCashierDataFromAPI();
      renderOrders();
      renderTables();
    }, 30000);

  } catch (err) {
    adminToast("Lỗi tải dữ liệu", "error");
  }
});
