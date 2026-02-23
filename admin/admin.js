// Wine Cellar 管理後台 JavaScript

// 配置
const API_BASE_URL = 'https://ai-wine-cellar.zeabur.app/api/v1/admin';
// const API_BASE_URL = 'http://localhost:8000/api/v1/admin'; // 本地開發使用

let authToken = localStorage.getItem('admin_token');
let charts = {};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    if (authToken) {
        showAdminPage();
        loadDashboard();
    } else {
        showLoginPage();
    }
});

// 顯示登入頁面
function showLoginPage() {
    document.getElementById('login-page').classList.remove('hidden');
    document.getElementById('admin-page').classList.add('hidden');
}

// 顯示管理頁面
function showAdminPage() {
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('admin-page').classList.remove('hidden');
}

// 登入處理
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('admin_token', authToken);
            showAdminPage();
            loadDashboard();
            errorDiv.classList.add('hidden');
        } else {
            errorDiv.textContent = '登入失敗，請檢查帳號密碼';
            errorDiv.classList.remove('hidden');
        }
    } catch (error) {
        errorDiv.textContent = '連接失敗，請稍後再試';
        errorDiv.classList.remove('hidden');
        console.error('Login error:', error);
    }
}

// 登出
function logout() {
    localStorage.removeItem('admin_token');
    authToken = null;
    showLoginPage();
    
    // 清理圖表
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
}

// API 請求封裝
async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        logout();
        return null;
    }
    
    return response.json();
}

// 側邊欄導航
function setActiveMenuItem(itemName) {
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 隱藏所有內容
    document.querySelectorAll('[id$="-content"]').forEach(content => {
        content.classList.add('hidden');
    });
    
    // 顯示對應內容
    document.getElementById(`${itemName}-content`).classList.remove('hidden');
    document.getElementById('page-title').textContent = getPageTitle(itemName);
}

function getPageTitle(itemName) {
    const titles = {
        'dashboard': 'Dashboard',
        'users': '用戶管理',
        'cellars': '酒窖管理',
        'wines': '酒款統計',
        'invitations': '邀請活動'
    };
    return titles[itemName] || 'Dashboard';
}

// Dashboard 相關函數
function showDashboard() {
    setActiveMenuItem('dashboard');
    loadDashboard();
}

async function loadDashboard() {
    try {
        const stats = await apiRequest('/dashboard/stats');
        if (!stats) return;
        
        // 更新統計數字
        document.getElementById('total-users').textContent = stats.overview.total_users;
        document.getElementById('total-cellars').textContent = stats.overview.total_cellars;
        document.getElementById('total-wines').textContent = stats.overview.total_wines;
        document.getElementById('total-invitations').textContent = stats.overview.total_invitations;
        
        document.getElementById('today-users').textContent = `+${stats.overview.today_new_users} 今日新增`;
        document.getElementById('today-wines').textContent = `+${stats.overview.today_new_wines} 今日新增`;
        document.getElementById('today-invitations').textContent = `+${stats.overview.today_new_invitations} 今日新增`;
        
        // 創建圖表
        createWineTypesChart(stats.wine_types);
        createPriceRangesChart(stats.price_ranges);
        createUserGrowthChart(stats.user_growth);
        
    } catch (error) {
        console.error('載入 Dashboard 失敗:', error);
    }
}

// 創建酒類統計圖表
function createWineTypesChart(data) {
    const ctx = document.getElementById('wine-types-chart');
    
    if (charts.wineTypes) {
        charts.wineTypes.destroy();
    }
    
    charts.wineTypes = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.type || '未分類'),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                    '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 創建價格分佈圖表
function createPriceRangesChart(data) {
    const ctx = document.getElementById('price-ranges-chart');
    
    if (charts.priceRanges) {
        charts.priceRanges.destroy();
    }
    
    charts.priceRanges = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.range),
            datasets: [{
                label: '酒款數量',
                data: data.map(item => item.count),
                backgroundColor: '#36A2EB'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 創建用戶增長圖表
function createUserGrowthChart(data) {
    const ctx = document.getElementById('user-growth-chart');
    
    if (charts.userGrowth) {
        charts.userGrowth.destroy();
    }
    
    charts.userGrowth = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.date),
            datasets: [{
                label: '新增用戶',
                data: data.map(item => item.count),
                borderColor: '#4BC0C0',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 用戶管理相關函數
function showUsers() {
    setActiveMenuItem('users');
    loadUsers();
}

async function loadUsers(page = 1, search = '') {
    try {
        const params = new URLSearchParams({ page, limit: 20 });
        if (search) params.append('search', search);
        
        const data = await apiRequest(`/users?${params}`);
        if (!data) return;
        
        displayUsersTable(data);
        
    } catch (error) {
        console.error('載入用戶列表失敗:', error);
    }
}

function displayUsersTable(data) {
    const container = document.getElementById('users-table');
    
    let html = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用戶</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LINE ID</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">統計</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">註冊時間</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
    `;
    
    data.users.forEach(user => {
        const createdAt = user.created_at ? new Date(user.created_at).toLocaleDateString('zh-TW') : '-';
        html += `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <img class="h-10 w-10 rounded-full" src="${user.picture_url || '/default-avatar.png'}" alt="">
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${user.display_name || '未設定'}</div>
                            <div class="text-sm text-gray-500">ID: ${user.id}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${user.line_user_id || '-'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${user.stats.cellars} 酒窖
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 ml-1">
                            ${user.stats.wines} 酒款
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 ml-1">
                            ${user.stats.invitations} 邀請
                        </span>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${createdAt}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <a href="#" onclick="viewUserDetail(${user.id})" class="text-indigo-600 hover:text-indigo-900">查看詳情</a>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        <div class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
            <div class="flex items-center justify-between">
                <div class="text-sm text-gray-700">
                    第 ${data.pagination.page} 頁，共 ${data.pagination.pages} 頁，總計 ${data.pagination.total} 位用戶
                </div>
                <div class="flex space-x-2">
    `;
    
    // 分頁按鈕
    if (data.pagination.page > 1) {
        html += `<button onclick="loadUsers(${data.pagination.page - 1})" class="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50">上一頁</button>`;
    }
    if (data.pagination.page < data.pagination.pages) {
        html += `<button onclick="loadUsers(${data.pagination.page + 1})" class="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50">下一頁</button>`;
    }
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 搜尋用戶
function searchUsers(event) {
    if (event.key === 'Enter') {
        const search = event.target.value;
        loadUsers(1, search);
    }
}

// 查看用戶詳情
async function viewUserDetail(userId) {
    try {
        const user = await apiRequest(`/users/${userId}`);
        if (!user) return;
        
        // 這裡可以打開一個模態窗口顯示用戶詳情
        // 暫時用 alert 顯示
        alert(`用戶詳情：\n姓名：${user.user.display_name}\n酒窖：${user.cellars.length} 個\n酒款：${user.recent_wines.length} 款\n邀請：${user.recent_invitations.length} 個`);
        
    } catch (error) {
        console.error('載入用戶詳情失敗:', error);
    }
}

// 其他頁面函數
function showCellars() {
    setActiveMenuItem('cellars');
    // TODO: 實現酒窖管理功能
}

function showWines() {
    setActiveMenuItem('wines');
    // TODO: 實現酒款統計功能
}

function showInvitations() {
    setActiveMenuItem('invitations');
    // TODO: 實現邀請活動管理功能
}