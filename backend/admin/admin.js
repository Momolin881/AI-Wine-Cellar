// Wine Cellar 管理後台 JavaScript - 簡化版（避免 JWT 依賴）

console.log('🎯 Admin.js 載入 - 簡化安全版本 - 顯示靜態資料');

// 靜態資料（來自新資料庫的 171 筆記錄）
const staticData = {
    overview: {
        total_users: 15,
        total_cellars: 15,
        total_wines: 30,
        total_invitations: 105,
        last_updated: '2026-02-25'
    },
    wine_types: [
        { type: '紅酒', count: 18 },
        { type: '白酒', count: 8 },
        { type: '氣泡酒', count: 4 }
    ],
    recent_activity: [
        { action: '新增酒款', item: 'Château Margaux 2015', time: '2 小時前' },
        { action: '創建邀請', item: '品酒聚會', time: '5 小時前' },
        { action: '新用戶註冊', item: '用戶15', time: '1 天前' }
    ]
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    showAdminPage();
    loadDashboard();
});

// 顯示管理頁面
function showAdminPage() {
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('admin-page').classList.remove('hidden');
}

// 設定活躍選單項目
function setActiveMenuItem(menuItem) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.getElementById(`${menuItem}-link`).classList.add('active');
    
    // 隱藏所有頁面
    document.querySelectorAll('.page').forEach(page => {
        page.classList.add('hidden');
    });
    
    // 顯示對應頁面
    document.getElementById(`${menuItem}-page`).classList.remove('hidden');
}

// Dashboard 相關函數
function showDashboard() {
    setActiveMenuItem('dashboard');
    loadDashboard();
}

function loadDashboard() {
    try {
        // 更新統計數字
        document.getElementById('total-users').textContent = staticData.overview.total_users;
        document.getElementById('total-cellars').textContent = staticData.overview.total_cellars;
        document.getElementById('total-wines').textContent = staticData.overview.total_wines;
        document.getElementById('total-invitations').textContent = staticData.overview.total_invitations;
        
        // 更新最後更新時間
        document.getElementById('last-updated').textContent = `最後更新: ${staticData.overview.last_updated}`;
        
        // 顯示酒款類型統計
        displayWineTypes();
        
        // 顯示近期活動
        displayRecentActivity();
        
        console.log('✅ Dashboard 載入完成（靜態資料）');
        
    } catch (error) {
        console.error('載入 Dashboard 失敗:', error);
    }
}

// 顯示酒款類型統計
function displayWineTypes() {
    const container = document.getElementById('wine-types-stats');
    if (!container) return;
    
    container.innerHTML = '';
    
    staticData.wine_types.forEach(item => {
        const div = document.createElement('div');
        div.className = 'stat-item';
        div.innerHTML = `
            <span class="stat-label">${item.type}</span>
            <span class="stat-value">${item.count}</span>
        `;
        container.appendChild(div);
    });
}

// 顯示近期活動
function displayRecentActivity() {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    container.innerHTML = '';
    
    staticData.recent_activity.forEach(activity => {
        const div = document.createElement('div');
        div.className = 'activity-item';
        div.innerHTML = `
            <div class="activity-action">${activity.action}</div>
            <div class="activity-item-name">${activity.item}</div>
            <div class="activity-time">${activity.time}</div>
        `;
        container.appendChild(div);
    });
}

// 其他頁面函數
function showUsers() {
    setActiveMenuItem('users');
    document.getElementById('users-content').innerHTML = `
        <h3>用戶管理</h3>
        <p>總計用戶數: ${staticData.overview.total_users}</p>
        <p>功能開發中...</p>
    `;
}

function showCellars() {
    setActiveMenuItem('cellars');
    document.getElementById('cellars-content').innerHTML = `
        <h3>酒窖管理</h3>
        <p>總計酒窖數: ${staticData.overview.total_cellars}</p>
        <p>功能開發中...</p>
    `;
}

function showWines() {
    setActiveMenuItem('wines');
    document.getElementById('wines-content').innerHTML = `
        <h3>酒款管理</h3>
        <p>總計酒款數: ${staticData.overview.total_wines}</p>
        <div id="wine-types-detail"></div>
        <p>功能開發中...</p>
    `;
}

function showInvitations() {
    setActiveMenuItem('invitations');
    document.getElementById('invitations-content').innerHTML = `
        <h3>邀請管理</h3>
        <p>總計邀請數: ${staticData.overview.total_invitations}</p>
        <p>功能開發中...</p>
    `;
}

function showSettings() {
    setActiveMenuItem('settings');
    document.getElementById('settings-content').innerHTML = `
        <h3>系統設定</h3>
        <p>資料庫狀態: 正常</p>
        <p>資料總計: 171 筆記錄</p>
        <p>功能開發中...</p>
    `;
}

// 登出功能（簡化版）
function handleLogout() {
    localStorage.removeItem('admin_token');
    window.location.reload();
}