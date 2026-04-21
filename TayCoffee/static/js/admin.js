const ADMIN_DATA = {
  products: [],
  orders: [],
  users: [],
  cashiers: [],
  promos: [], // Will load from API
  revenue: [
    { day: "Mon", amount: 840 },
    { day: "Tue", amount: 1220 },
    { day: "Wed", amount: 980 },
    { day: "Thu", amount: 1540 },
    { day: "Fri", amount: 1890 },
    { day: "Sat", amount: 2340 },
    { day: "Sun", amount: 1650 },
  ],
};

const SESSION_USER_KEY = "tay_coffee_current_user";
const SESSION_STORAGE_KEY = "tay_coffee_current_user_email";

const STATUS_MAP = {
  pending: { label: "Đang chờ", cls: "sbadge-warning" },
  preparing: { label: "Chuẩn bị", cls: "sbadge-warning" },
  served: { label: "Đã giao", cls: "sbadge-info" },
  completed: { label: "Xong", cls: "sbadge-success" },
  cancelled: { label: "Hủy", cls: "sbadge-danger" },
};

let unsubscribeOrdersRealtime = null;
let editingId = null;
let editingUserId = null;
let editingUserRole = "staff";
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
    if (typeof mq.addEventListener === "function") {
      mq.addEventListener("change", update);
    } else if (typeof mq.addListener === "function") {
      mq.addListener(update);
    }
  });

  update();
}

function getAdminApiBase() {
  if (typeof window === "undefined") return "/api";
  const { protocol, hostname, port, host } = window.location;
  if (port === "5501") return `${protocol}//${hostname}:5500/api`;
  return `${protocol}//${host}/api`;
}

async function fetchItems(path, limit = 200) {
  const url = `${getAdminApiBase()}${path}?limit=${encodeURIComponent(limit)}`;
  const res = await fetch(url);
  const text = await res.text();
  if (!text) return [];
  const data = JSON.parse(text);
  if (!res.ok) throw new Error(data.error || `Request failed: ${path}`);
  return Array.isArray(data.items) ? data.items : [];
}

async function fetchAdminUsers(role, limit = 200) {
  const params = new URLSearchParams();
  params.set("limit", limit);
  if (role) params.set("role", role);
  const url = `${getAdminApiBase()}/admin/users?${params.toString()}`;
  const res = await fetch(url);
  const text = await res.text();
  if (!text) return [];
  const data = JSON.parse(text);
  if (!res.ok) throw new Error(data.error || "Request failed: admin users");
  return Array.isArray(data.items) ? data.items : [];
}

function adminToast(msg, type = "info") {
  const icons = {
    default: '<i class="fa-solid fa-fire"></i>',
    success: '<i class="fa-solid fa-circle-check"></i>',
    error: '<i class="fa-solid fa-circle-exclamation"></i>',
    info: '<i class="fa-solid fa-circle-info"></i>',
    warning: '<i class="fa-solid fa-triangle-exclamation"></i>',
  };
  
  let container = document.getElementById("toast-container");
  if (!container) return; // Should exist in dashboard.html

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    display:flex; align-items:center; gap:12px;
    background: var(--bg-surface);
    color: var(--white);
    padding: 14px 24px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    border: 1px solid var(--glass-border);
    animation: fadeInUp .3s ease forwards;
    margin-bottom: 12px;
  `;
  
  const iconSpan = `<span style="color:var(--gold); font-size:18px">${icons[type] || icons.default}</span>`;
  toast.innerHTML = `${iconSpan} <span>${msg}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.4s";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

function formatOrderDisplayId(dbId) {
  return `#TC-${String(dbId).padStart(4, "0")}`;
}

function parseAmount(v) {
  if (typeof v === "number") return v;
  return Number(String(v || "").replace("$", "")) || 0;
}

function mapCategory(categoryId) {
  const n = Number(categoryId);
  if (n === 1) return "☕ Cà phê";
  if (n === 2) return "🍵 Trà";
  if (n === 3) return "🧁 Bánh ngọt";
  return "📦 Khác";
}

function showPanel(id, el) {
  document
    .querySelectorAll(".a-panel")
    .forEach((p) => p.classList.remove("active"));
  document
    .querySelectorAll(".a-nav-item")
    .forEach((n) => n.classList.remove("active"));
  const panel = document.getElementById("panel-" + id);
  if (panel) panel.classList.add("active");
  if (el) el.classList.add("active");
}

function filterTable(tbodyId, query) {
  const q = String(query || "").toLowerCase();
  document.querySelectorAll("#" + tbodyId + " tr").forEach((tr) => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
  });
}

function debouncedFilterTable(tbodyId, query, delay = 180) {
  clearTimeout(filterTimers[tbodyId]);
  filterTimers[tbodyId] = setTimeout(() => filterTable(tbodyId, query), delay);
}

async function loadAdminDataFromAPI() {
  try {
    console.log("[Manager] Starting data load from backend API...");

    let products = [];
    let customerUsers = [];
    let shipperUsers = [];
    let orders = [];

    // Load products, users, orders in parallel from backend
    // NOTE: We skip Supabase REST directly because publishable key is not a valid JWT anon key.
    //       All data comes from the Flask backend which uses the service role key safely.
    try {
      if (
        typeof APIClient !== "undefined" &&
        APIClient.getProducts &&
        APIClient.getAdminUsers &&
        APIClient.getOrders
      ) {
        console.log("[Manager] Using APIClient to load all data...");
        [products, orders, customerUsers, shipperUsers] = await Promise.all([
          APIClient.getProducts(300),
          APIClient.getOrders(300),
          APIClient.getAdminUsers("staff", 300),
          APIClient.getAdminUsers("cashier", 300),
        ]);
      } else {
        console.log(
          "[Manager] APIClient not available, using fetchItems fallback...",
        );
        [products, orders, customerUsers, shipperUsers] = await Promise.all([
          fetchItems("/products", 300),
          fetchItems("/orders", 300),
          fetchAdminUsers("staff", 300),
          fetchAdminUsers("cashier", 300),
        ]);
      }
      console.log(
        "[Manager] Raw API response - products:",
        products.length,
        "customers:",
        customerUsers.length,
        "cashiers:",
        shipperUsers.length,
        "orders:",
        orders.length,
      );
    } catch (err) {
      console.error("[Manager] Failed to load data from backend:", err);
      products = products || [];
      customerUsers = customerUsers || [];
      shipperUsers = shipperUsers || [];
      orders = orders || [];
    }

    const safeDate = (value) => {
      if (!value) return "-";
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return "-";
      return parsed.toISOString().slice(0, 10);
    };

    // Map products
    ADMIN_DATA.products = (products || []).map((p) => ({
      id: Number(p.productid),
      name: p.productname || "Unnamed product",
      categoryid: p.categoryid,
      cat: mapCategory(p.categoryid),
      price: Number(p.price || 0),
      available: p.isactive !== false,
      imageurl: p.imageurl || "",
      emoji: typeof p.emoji === "string" ? p.emoji : "",
    }));

    // Map orders first to build aggregates for users & shippers
    const ordersByCustomer = {};
    const ordersByShipper = {};

    ADMIN_DATA.orders = (orders || []).map((o) => {
      const dbId = Number(o.orderid);
      const customerId = Number(o.customerid) || null;
      const shipperId = Number(o.shipperid) || null;
      if (customerId) {
        ordersByCustomer[customerId] = (ordersByCustomer[customerId] || 0) + 1;
      }
      if (shipperId) {
        ordersByShipper[shipperId] = (ordersByShipper[shipperId] || 0) + 1;
      }
      return {
        id: formatOrderDisplayId(o.orderid),
        dbId,
        customerId,
        shipperId,
        customer: o.customer_name || (customerId ? `Customer #${customerId}` : 'Customer'),
        items: o.items_summary || 'Xem chi tiết',
        subtotal: Number(o.subtotal || 0),
        shipping: Number(o.shippingfee || 0),
        discount: Number(o.discount || 0),
        get total() {
          return (this.subtotal + this.shipping) - this.discount;
        },
        shipper: o.tablenumber ? `Bàn ${o.tablenumber}` : (o.table_id ? `Bàn ${o.table_id}` : '-'),
        tableNumber: o.tablenumber || o.table_id || '-',
        status: o.orderstatus || 'pending',
        date: o.orderdate ? new Date(o.orderdate).toLocaleString('vi-VN') : '-',
        notes: o.notes || '',
        address: '-', // Not needed for in-store
      };
    });

    // Map customers & shippers from admin endpoints
    ADMIN_DATA.users = (customerUsers || []).map((u) => {
      const id = Number(u.id || u.userid);
      return {
        id,
        name: u.name || u.fullname || "Unknown",
        email: u.email || "-",
        phone: u.phone || "-",
        roleid: 3,
        joined: safeDate(u.created_at || u.createdat),
        orders: ordersByCustomer[id] || 0,
        active: u.is_active !== false,
      };
    });

    ADMIN_DATA.cashiers = (shipperUsers || []).map((u) => {
      const id = Number(u.id || u.userid);
      const active = u.is_active !== false;
      return {
        id,
        name: u.name || u.fullname || "Unknown",
        phone: u.phone || "-",
        email: u.email || "-",
        completed: ordersByShipper[id] || 0,
        status: active ? "online" : "offline",
        active,
      };
    });

    console.log("[Manager] ✅ Data loaded successfully:", {
      products: ADMIN_DATA.products.length,
      users: ADMIN_DATA.users.length,
      orders: ADMIN_DATA.orders.length,
      cashiers: ADMIN_DATA.cashiers.length,
    });
  } catch (err) {
    console.error("[Manager] CRITICAL - Data load failed:", err);
    adminToast(`Cannot load dashboard data: ${err.message || err}`, "error");
  }
}

function renderStats() {
  try {
    const deliveredRevenue = (ADMIN_DATA.orders || [])
      .filter((o) => o.status === "completed")
      .reduce((sum, o) => sum + parseAmount(o.total), 0);

    const statRevenue = document.getElementById("stat-revenue");
    const statOrders = document.getElementById("stat-orders");
    const statUsers = document.getElementById("stat-users");
    const statTables = document.getElementById("stat-tables");

    if (statRevenue)
      statRevenue.textContent = deliveredRevenue.toLocaleString('vi-VN') + "₫";
    if (statOrders) statOrders.textContent = (ADMIN_DATA.orders || []).length;
    if (statUsers) statUsers.textContent = (ADMIN_DATA.users || []).length;
    if (statTables) {
       const activeTableCount = new Set((ADMIN_DATA.orders || []).filter(o => !['completed', 'cancelled'].includes(o.status)).map(o => o.tableNumber)).size;
       statTables.textContent = activeTableCount;
    }
  } catch (err) {
    console.error("[Manager] renderStats error:", err);
  }
}

function renderRevenueChart() {
  try {
    const wrap = document.getElementById("revenue-chart");
    if (!wrap) return;
    const data = ADMIN_DATA.revenue;
    if (!data || !data.length) return;
    const max = Math.max(...data.map((d) => d.amount));
    wrap.innerHTML = data
      .map((d) => {
        const pct = max > 0 ? ((d.amount / max) * 100).toFixed(1) : 0;
        return `<div class="chart-bar-item">
        <div class="chart-bar-label">${d.day}</div>
        <div class="chart-bar-track"><div class="chart-bar-fill" style="width:${pct}%"></div></div>
        <div class="chart-bar-val">${d.amount.toLocaleString('vi-VN')}₫</div>
      </div>`;
      })
      .join("");
  } catch (err) {
    console.error("[Manager] renderRevenueChart error:", err);
  }
}



function renderRecentOrders() {
  const tbody = document.getElementById("recent-orders-body");
  if (!tbody) return;
  const recent = (ADMIN_DATA.orders || []).slice(0, 5);
  if (recent.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="table-empty">No recent activity</td></tr>';
    return;
  }
  tbody.innerHTML = recent
      .map((o) => {
        const s = STATUS_MAP[o.status] || { label: o.status, cls: "sbadge-info" };
        return `<tr>
        <td style="font-weight:700; color:var(--white)">${o.id}</td>
        <td style="font-weight:600">${o.customer}</td>
        <td style="max-width:180px; font-size:12px; opacity:0.75">${o.items}</td>
        <td style="color:var(--gold); font-weight:700">${parseAmount(o.total).toLocaleString('vi-VN')}₫</td>
        <td><span class="sbadge ${s.cls}">${s.label}</span></td>
        <td style="font-size:12px; opacity:0.5">${o.date}</td>
      </tr>`;
      })
      .join("");
}

function renderProducts() {
  try {
    const tbody = document.getElementById("products-body");
    if (!tbody) return;
    if (!ADMIN_DATA.products || ADMIN_DATA.products.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="table-empty">No products in inventory</td></tr>';
      return;
    }
    tbody.innerHTML = ADMIN_DATA.products
      .map((p) => `<tr>
      <td style="font-weight:700; color:var(--white)">${p.emoji} ${p.name}</td>
      <td><span style="padding:4px 10px; background:rgba(255,255,255,0.05); border-radius:6px; font-size:12px">${p.cat}</span></td>
      <td style="color:var(--gold); font-weight:700">${p.price.toLocaleString('vi-VN')}₫</td>
      <td><span class="sbadge ${p.available ? "sbadge-success" : "sbadge-danger"}">${p.available ? "Hệ thống hiển thị" : "Tạm ẩn"}</span></td>
      <td>
        <div class="abtns">
          <button class="abtn abtn-view" onclick="editProduct(${p.id})"><i class="fa-solid fa-pen-to-square"></i></button>
          <button class="abtn" onclick="deleteProduct(${p.id})" style="border-color:rgba(231,76,60,0.2); color:#e74c3c"><i class="fa-solid fa-trash"></i></button>
        </div>
      </td>
    </tr>`).join("");
  } catch (err) {
    console.error("[Manager] renderProducts error:", err);
  }
}

function renderOrders() {
  const tbody = document.getElementById("orders-body");
  if (!tbody) return;
  const orders = ADMIN_DATA.orders || [];
  if (orders.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="table-empty">No order history found</td></tr>';
    return;
  }

  tbody.innerHTML = orders
      .map((o) => {
        const s = STATUS_MAP[o.status] || { label: o.status, cls: "sbadge-info" };
        const statusOptions = Object.keys(STATUS_MAP)
          .map(k => `<option value="${k}" ${k === o.status ? "selected" : ""}>${STATUS_MAP[k].label}</option>`)
          .join("");
        const notesHtml = o.notes ? `<div style="font-size:11px; color:var(--gold); margin-top:4px; font-style:italic; opacity:0.8"><i class="fa-solid fa-comment-dots"></i> ${o.notes}</div>` : '';
        return `<tr>
        <td style="font-weight:700; color:var(--white)">${o.id}</td>
        <td style="font-weight:600">${o.customer}</td>
        <td style="max-width:200px"><div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis">${o.items}</div>${notesHtml}</td>
        <td style="color:var(--gold); font-weight:700">${parseAmount(o.total).toLocaleString('vi-VN')}₫</td>
        <td><span style="padding:4px 8px; background:rgba(255,255,255,0.05); border-radius:4px">${o.tableNumber}</span></td>
        <td>
          <span class="sbadge ${s.cls}">${s.label}</span>
          <select class="status-select" onchange="updateOrderStatus('${o.id}', this.value)" style="width:auto; margin-left:8px">
            ${statusOptions}
          </select>
        </td>
        <td style="font-size:12px; opacity:0.6">${o.date}</td>
        <td><button class="abtn abtn-view" onclick="openOrderDetails('${o.id}')"><i class="fa-solid fa-eye"></i></button></td>
      </tr>`;
      }).join("");
}

async function updateOrderStatus(orderId, status) {
  const order = ADMIN_DATA.orders.find((o) => o.id === orderId);
  if (!order) return;

  try {
    await APIClient.updateOrderStatus(order.dbId, status);
    order.status = status;
    renderStats();
    renderRecentOrders();
    renderOrders();
    adminToast(`Updated ${orderId}`, "success");
  } catch (err) {
    adminToast(`Update failed: ${err.message || err}`, "error");
    if (typeof renderOrders === "function") renderOrders();
  }
}

function renderUsers() {
  try {
    const tbody = document.getElementById("users-body");
    if (!tbody) return;

    const staffs = (ADMIN_DATA.users || []).map(u => ({ ...u, displayRole: 'Staff', icon: 'fa-user-tie' }));
    const cashiers = (ADMIN_DATA.cashiers || []).map(c => ({ ...c, displayRole: 'Cashier', icon: 'fa-cash-register' }));
    const allPersonnel = [...staffs, ...cashiers];

    if (allPersonnel.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No personnel found</td></tr>';
      return;
    }

    tbody.innerHTML = allPersonnel
      .map((u) => {
        const statusClass = u.active ? "sbadge-success" : "sbadge-danger";
        const statusLabel = u.active ? "Online" : "Offline";
        return `<tr>
        <td style="font-weight:700; color:var(--white)"><i class="fa-solid ${u.icon}" style="margin-right:8px; opacity:0.6"></i>${u.name}</td>
        <td style="font-size:12px">${u.email}<br/><span style="opacity:0.5">${u.phone}</span></td>
        <td><span style="font-weight:700; color:var(--gold)">${u.displayRole}</span></td>
        <td>${u.orders || u.completed || 0} tasks</td>
        <td style="font-size:12px; opacity:0.6">${u.joined || '-'}</td>
        <td><span class="sbadge ${statusClass}">${statusLabel}</span></td>
        <td>
          <div class="abtns">
            <button class="abtn abtn-view" onclick="openUserModal('${u.displayRole.toLowerCase()}', ${u.id})"><i class="fa-solid fa-user-pen"></i></button>
            <button class="abtn" onclick="deleteAdminUser(${u.id})" style="border-color:rgba(231,76,60,0.2); color:#e74c3c"><i class="fa-solid fa-user-xmark"></i></button>
          </div>
        </td>
      </tr>`;
      }).join("");
  } catch (err) {
    console.error("[Manager] renderUsers error:", err);
  }
}


function renderPromos() {
  const tbody = document.getElementById("promos-body");
  if (!tbody) {
    console.warn("[Manager] promos-body element not found");
    return;
  }
  if (
    !ADMIN_DATA.promos ||
    !Array.isArray(ADMIN_DATA.promos) ||
    ADMIN_DATA.promos.length === 0
  ) {
    tbody.innerHTML =
      '<tr><td colspan="7" class="table-empty">No promotions</td></tr>';
    return;
  }
  tbody.innerHTML = ADMIN_DATA.promos
    .map(
      (p) => `<tr>
    <td>${p.code || "-"}</td>
    <td>${p.discount || "-"}</td>
    <td>${p.minOrder || "-"}</td>
    <td>${p.used || 0}</td>
    <td>${p.expires || "-"}</td>
    <td><span class="sbadge ${p.active ? "sbadge-success" : "sbadge-danger"}">${p.active ? "Active" : "Expired"}</span></td>
    <td><button class="abtn abtn-edit" onclick="showAdminToast('Promo ${p.code}')">Edit</button></td>
  </tr>`,
    )
    .join("");
}

function openProductModal(id = null) {
  editingId = id;
  const modal = document.getElementById("product-modal");
  if (!modal) return;

  const modalTitle = document.getElementById("prod-modal-title");

  // Populate form with existing product data if editing
  if (id) {
    const product = ADMIN_DATA.products.find((p) => p.id === Number(id));
    if (product) {
      if (modalTitle) modalTitle.textContent = "EDIT PRODUCT";
      document.getElementById("p-name").value =
        product.name || product.productname || "";
      document.getElementById("p-price").value = product.price || "";
      document.getElementById("p-desc").value = product.description || "";
      document.getElementById("p-cat").value =
        product.categoryid || product.category || "";
      document.getElementById("p-emoji").value = product.emoji || "";
      document.getElementById("p-avail").value = product.available
        ? "true"
        : "false";
      document.getElementById("p-tags").value = product.tags || "";
    }
  } else {
    // Clear form for new product
    if (modalTitle) modalTitle.textContent = "ADD PRODUCT";
    document.getElementById("p-name").value = "";
    document.getElementById("p-price").value = "";
    document.getElementById("p-desc").value = "";
    document.getElementById("p-cat").value = "1";
    document.getElementById("p-emoji").value = "";
    document.getElementById("p-avail").value = "true";
    document.getElementById("p-tags").value = "";
  }

  modal.classList.remove("hidden");
}

function editProduct(id) {
  openProductModal(id);
}

function closeProductModal() {
  const modal = document.getElementById("product-modal");
  if (!modal) return;
  const imageInput = document.getElementById("p-image-file");
  if (imageInput) imageInput.value = "";
  modal.classList.add("hidden");
}

async function saveProduct() {
  try {
    // Collect form data
    const metadata = {
      productname: (document.getElementById("p-name").value || "").trim(),
      price: parseFloat(document.getElementById("p-price").value) || 0,
      description: (document.getElementById("p-desc").value || "").trim(),
      categoryid: (document.getElementById("p-cat").value || "").trim(),
      emoji: (document.getElementById("p-emoji").value || "").trim(),
      isactive: document.getElementById("p-avail").value === "true",
      tags: (document.getElementById("p-tags").value || "").trim(),
    };

    // Validate required fields
    if (!metadata.productname) {
      adminToast("Product name is required", "error");
      return;
    }
    if (metadata.price <= 0) {
      adminToast("Price must be greater than 0", "error");
      return;
    }

    let createdProductId = editingId;

    // Create or update metadata
    if (editingId) {
      // UPDATE existing product
      await APIClient.updateProductMetadata(editingId, metadata);
      adminToast("Product details updated", "success");
    } else {
      // CREATE new product
      const response = await APIClient.createProduct(metadata);
      if (response.product && response.product.productid) {
        createdProductId = response.product.productid;
        editingId = createdProductId;
        adminToast("Product created successfully", "success");
      } else {
        throw new Error("Failed to get product ID from response");
      }
    }

    // Then handle image upload if selected
    const imageInput = document.getElementById("p-image-file");
    const file = imageInput && imageInput.files ? imageInput.files[0] : null;

    if (file) {
      if (
        window.SupabaseWeb &&
        typeof window.SupabaseWeb.uploadProductImage === "function"
      ) {
        // USE SUPABASE (Cloud)
        try {
          const upload = await window.SupabaseWeb.uploadProductImage(
            file,
            createdProductId,
            "product-images",
          );
          await APIClient.updateProductImage(createdProductId, upload.publicUrl);
          adminToast("Image uploaded to Supabase", "success");
        } catch (err) {
          adminToast(`Supabase upload failed: ${err.message || err}`, "error");
        }
      } else {
        // USE LOCAL (Flask)
        try {
          console.log("[Manager] Falling back to local image upload...");
          const res = await APIClient.uploadProductImageLocal(createdProductId, file);
          if (res.ok) {
            adminToast("Image uploaded locally", "success");
          } else {
            throw new Error(res.error || "Local upload failed");
          }
        } catch (err) {
          adminToast(`Local upload failed: ${err.message || err}`, "error");
        }
      }
    }

    // Update local data and refresh UI
    const product = ADMIN_DATA.products.find(
      (p) => p.id === Number(createdProductId),
    );
    if (product) {
      // Sync names between API format and UI format
      product.name = metadata.productname;
      product.productname = metadata.productname;
      product.price = metadata.price;
      product.description = metadata.description;
      product.categoryid = metadata.categoryid;
      product.cat = mapCategory(metadata.categoryid);
      product.emoji = metadata.emoji;
      product.available = metadata.isactive;
      product.isactive = metadata.isactive;
      product.tags = metadata.tags;
    }

    closeProductModal();
    await loadAdminDataFromAPI();
    renderProducts();
  } catch (err) {
    adminToast(`Save failed: ${err.message || err}`, "error");
  }
}

function getUserCollection(role) {
  return role === "cashier" ? ADMIN_DATA.cashiers : ADMIN_DATA.users;
}

function openUserModal(role = "customer", userId = null) {
  editingUserRole = role;
  editingUserId = userId;
  const modal = document.getElementById("user-modal");
  if (!modal) return;

  const title = document.getElementById("user-modal-title");
  const nameInput = document.getElementById("u-name");
  const emailInput = document.getElementById("u-email");
  const phoneInput = document.getElementById("u-phone");
  const passwordInput = document.getElementById("u-password");
  const badge = document.getElementById("u-status-pill");
  const submitBtn = document.getElementById("user-modal-submit");

  const roleLabel = role === "cashier" ? "Thu ngân" : "Nhân viên phục vụ";
  if (title) title.textContent = `${userId ? "Cập nhật" : "Tạo mới"} ${roleLabel}`;
  if (badge) {
    badge.textContent = roleLabel;
    badge.className = `sbadge ${role === "cashier" ? "sbadge-info" : "sbadge-success"}`;
  }

  const existing = userId
    ? getUserCollection(role).find((u) => Number(u.id) === Number(userId))
    : null;
  nameInput.value = existing ? existing.name : "";
  emailInput.value = existing ? existing.email : "";
  emailInput.disabled = Boolean(existing);
  phoneInput.value = existing
    ? existing.phone === "-"
      ? ""
      : existing.phone
    : "";
  passwordInput.value = "";
  passwordInput.placeholder = existing
    ? "Bỏ trống nếu không đổi mật khẩu"
    : "Mật khẩu tạm thời (tối thiểu 8 ký tự)";
  submitBtn.textContent = existing ? "Lưu thay đổi" : "Tạo người dùng";

  modal.classList.remove("hidden");
}

function closeUserModal() {
  const modal = document.getElementById("user-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  editingUserId = null;
}

async function saveUserInfo() {
  const nameInput = document.getElementById("u-name");
  const emailInput = document.getElementById("u-email");
  const phoneInput = document.getElementById("u-phone");
  const passwordInput = document.getElementById("u-password");

  const payload = {
    role: editingUserRole,
    full_name: (nameInput.value || "").trim(),
    phone: (phoneInput.value || "").trim() || null,
  };

  if (!payload.full_name) {
    adminToast("Please enter full name", "warning");
    return;
  }

  try {
    if (editingUserId) {
      if (passwordInput.value) {
        payload.password = passwordInput.value;
      }
      if (!emailInput.disabled) {
        payload.email = (emailInput.value || "").trim().toLowerCase();
      }
      await APIClient.updateAdminUser(editingUserId, payload);
      adminToast("User updated successfully", "success");
    } else {
      payload.email = (emailInput.value || "").trim().toLowerCase();
      payload.password = passwordInput.value;
      if (!payload.email || !payload.password) {
        adminToast("Email và mật khẩu là bắt buộc", "warning");
        return;
      }
      await APIClient.createAdminUser(payload);
      adminToast("User created successfully", "success");
    }

    closeUserModal();
    await loadAdminDataFromAPI();
    renderStats();
    renderUsers();
  } catch (err) {
    adminToast(err.message || "Operation failed", "error");
  }
}

async function deleteAdminUser(userId) {
  if (!confirm("Are you sure you want to delete this account?")) return;
  try {
    const res = await APIClient.deleteAdminUser(userId);
    adminToast(res.message || "User deleted", "success");
    await loadAdminDataFromAPI();
    renderStats();
    renderRecentOrders();
    renderProducts();
    renderOrders();
    renderUsers();
    renderPromos();
  } catch (err) {
    adminToast(err.message || "Delete failed", "error");
  }
}

async function deleteProduct(id) {
  if (!confirm("Are you sure you want to delete this product?")) return;
  try {
    const response = await APIClient.deleteProduct(id);
    // Reload data from backend to ensure soft-deleted items are correctly rendered
    await loadAdminDataFromAPI();
    renderStats();
    renderProducts();
    adminToast(response.message || "Product deleted/deactivated", "success");
  } catch (err) {
    console.error(err);
    adminToast(err.message || "Failed to delete product", "error");
  }
}

function showAdminToast(msg) {
  adminToast(msg, "info");
}

function openOrderDetails(orderId) {
  const modal = document.getElementById("order-modal");
  if (!modal) return;
  const order = ADMIN_DATA.orders.find((o) => o.id === orderId);
  if (!order) {
    adminToast("Không tìm thấy đơn hàng", "error");
    return;
  }
  const fields = {
    'order-detail-id': order.id,
    'order-detail-customer': order.customer,
    'order-detail-shipper': order.tableNumber, // Reusing ID for simplicity
    'order-detail-subtotal': `${parseAmount(order.subtotal).toLocaleString('vi-VN')}₫`,
    'order-detail-total': `${parseAmount(order.total).toLocaleString('vi-VN')}₫`,
    'order-detail-status': STATUS_MAP[order.status]?.label || order.status,
    'order-detail-date': order.date,
    'order-detail-items': order.items || '-',
    'order-detail-notes': order.notes || '-',
  };
  Object.keys(fields).forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.textContent = fields[id];
  });
  modal.classList.remove("hidden");
}



function closeOrderModal() {
  const modal = document.getElementById("order-modal");
  if (!modal) return;
  modal.classList.add("hidden");
}

function updateClock() {
  const el = document.getElementById("admin-clock");
  if (!el) return;
  el.textContent = new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function initPollingRefresh() {
  // Poll every 30s for updates (replaces Supabase realtime for local LAN)
  setInterval(async () => {
    try {
      await loadAdminDataFromAPI();
      renderStats();
      renderRecentOrders();
      renderProducts();
      renderOrders();
      renderUsers();
      renderPromos();
    } catch (err) {
      console.warn('[Manager] Polling refresh failed:', err);
    }
  }, 30000);
}

async function logout() {
  try {
    localStorage.removeItem(SESSION_USER_KEY);
    localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch (err) {
    console.warn("[Manager] Failed to clear session storage:", err);
  }

  adminToast("Đã đăng xuất. Hẹn gặp lại!", "info");
  setTimeout(() => {
    window.location.href = "/index.html";
  }, 800);
}

document.addEventListener("DOMContentLoaded", async () => {
  console.log("[Manager] DOMContentLoaded event fired");
  try {
    initContrastModeWatcher();
    console.log("[Manager] Calling loadAdminDataFromAPI...");
    await loadAdminDataFromAPI();
    console.log('[Manager] Data load complete, rendering...');
    renderStats();
    renderRevenueChart();
    renderRecentOrders();
    renderProducts();
    renderOrders();
    renderUsers();
    renderPromos();

    updateClock();
    setInterval(updateClock, 1000);

    console.log('[Manager] Initializing polling refresh...');
    initPollingRefresh();
    console.log("[Manager] Dashboard fully loaded!");
  } catch (err) {
    console.error("[Manager] DOMContentLoaded error:", err);
    adminToast(
      `Dashboard initialization failed: ${err.message || err}`,
      "error",
    );
  }
});

// No cleanup needed - polling stops automatically on page unload
