/**
 * 酒窖首頁 - 酒款清單
 *
 * 顯示所有酒款，支援篩選（酒類）和搜尋。
 * 主要功能：拍照入庫、酒款展示（正方形卡片網格）
 * Neumorphism 深色主題
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Layout,
    Card,
    Spin,
    Empty,
    message,
    Typography,
    Input,
    Tag,
    Statistic,
    Row,
    Col,
} from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import {
    PhotoUploadButton,
    WineCardSquare,
    FloatAddButton,
    VersionFooter,
} from '../components';
import '../styles/WineCardSquare.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function WineHome() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [wineItems, setWineItems] = useState([]);
    const [filteredItems, setFilteredItems] = useState([]);
    const [searchText, setSearchText] = useState('');
    const [wineTypeFilter, setWineTypeFilter] = useState('all');

    // 統計資料
    const [stats, setStats] = useState({
        totalWines: 0,
        totalValue: 0,
        unopened: 0,
        opened: 0,
    });

    const wineTypes = ['紅酒', '白酒', '氣泡酒', '香檳', '威士忌', '白蘭地', '清酒', '啤酒', '其他'];

    useEffect(() => {
        loadData();
    }, [wineTypeFilter]);

    useEffect(() => {
        // 搜尋篩選
        let result = wineItems;
        if (searchText) {
            result = result.filter((item) =>
                item.name.toLowerCase().includes(searchText.toLowerCase()) ||
                item.brand?.toLowerCase().includes(searchText.toLowerCase()) ||
                item.region?.toLowerCase().includes(searchText.toLowerCase())
            );
        }
        setFilteredItems(result);
    }, [wineItems, searchText]);

    const loadData = async () => {
        try {
            setLoading(true);

            // 取得酒款列表（只取在庫的）
            let url = `${API_BASE}/api/v1/wine-items?status=active`;
            if (wineTypeFilter !== 'all') {
                url += `&wine_type=${wineTypeFilter}`;
            }

            const itemsRes = await fetch(url, {
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const itemsData = await itemsRes.json();
            setWineItems(itemsData);
            setFilteredItems(itemsData);

            // 計算統計
            setStats({
                totalWines: itemsData.length,
                totalValue: itemsData.reduce((sum, i) => sum + (i.total_value || 0), 0),
                unopened: itemsData.filter(i => i.bottle_status === 'unopened').length,
                opened: itemsData.filter(i => i.bottle_status === 'opened').length,
            });

        } catch (error) {
            console.error('載入資料失敗:', error);
            message.error('載入資料失敗');
        } finally {
            setLoading(false);
        }
    };

    const handleCardClick = (item) => {
        navigate(`/edit/${item.id}`);
    };

    return (
        <Layout style={{ minHeight: '100vh', background: '#1a1a1a' }}>
            <Content style={{ padding: '16px', maxWidth: 480, margin: '0 auto' }}>
                {/* 標題 */}
                <div style={{ marginBottom: 16 }}>
                    <Title level={2} style={{ marginBottom: 4, color: '#f5f5f5' }}>
                        🍷 我的酒窖
                    </Title>
                    <Text style={{ color: '#888' }}>個人數位酒窖管理</Text>
                </div>

                {/* 拍照入庫按鈕 - 主要 CTA */}
                <div style={{ marginBottom: 20 }}>
                    <PhotoUploadButton onClick={() => navigate('/add')} />
                </div>

                {/* 統計看板 */}
                <Card
                    style={{
                        marginBottom: 20,
                        background: '#2d2d2d',
                        border: 'none',
                        borderRadius: 12,
                    }}
                    bodyStyle={{ padding: '16px' }}
                >
                    <Row gutter={8}>
                        <Col span={6}>
                            <Statistic
                                title={<span style={{ color: '#888', fontSize: 12 }}>總酒數</span>}
                                value={stats.totalWines}
                                suffix="款"
                                valueStyle={{ color: '#f5f5f5', fontSize: 20 }}
                            />
                        </Col>
                        <Col span={6}>
                            <Statistic
                                title={<span style={{ color: '#888', fontSize: 12 }}>未開封</span>}
                                value={stats.unopened}
                                suffix="瓶"
                                valueStyle={{ color: '#c9a227', fontSize: 20 }}
                            />
                        </Col>
                        <Col span={6}>
                            <Statistic
                                title={<span style={{ color: '#888', fontSize: 12 }}>已開瓶</span>}
                                value={stats.opened}
                                suffix="瓶"
                                valueStyle={{ color: '#f5f5f5', fontSize: 20 }}
                            />
                        </Col>
                        <Col span={6}>
                            <Statistic
                                title={<span style={{ color: '#888', fontSize: 12 }}>總價值</span>}
                                value={stats.totalValue}
                                prefix="$"
                                precision={0}
                                valueStyle={{ color: '#f5f5f5', fontSize: 20 }}
                            />
                        </Col>
                    </Row>
                </Card>

                {/* 搜尋 */}
                <div style={{ marginBottom: 12 }}>
                    <Search
                        placeholder="搜尋酒款..."
                        allowClear
                        onSearch={setSearchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        style={{ width: '100%' }}
                    />
                </div>

                {/* 酒類篩選標籤 */}
                <div style={{ marginBottom: 16, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <Tag
                        color={wineTypeFilter === 'all' ? 'gold' : 'default'}
                        onClick={() => setWineTypeFilter('all')}
                        style={{ cursor: 'pointer', borderRadius: 16 }}
                    >
                        全部
                    </Tag>
                    {wineTypes.map(type => (
                        <Tag
                            key={type}
                            color={wineTypeFilter === type ? 'gold' : 'default'}
                            onClick={() => setWineTypeFilter(type)}
                            style={{ cursor: 'pointer', borderRadius: 16 }}
                        >
                            {type}
                        </Tag>
                    ))}
                </div>

                {/* 酒款正方形卡片網格 */}
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <Spin size="large" />
                    </div>
                ) : filteredItems.length === 0 ? (
                    <Empty
                        description={
                            <span style={{ color: '#888' }}>
                                {wineItems.length === 0
                                    ? "還沒有酒款，新增你的第一支酒吧！"
                                    : "沒有符合條件的酒款"}
                            </span>
                        }
                        style={{ padding: '40px 0' }}
                    />
                ) : (
                    <div className="wine-grid">
                        {filteredItems.map((item) => (
                            <WineCardSquare
                                key={item.id}
                                item={item}
                                onClick={() => handleCardClick(item)}
                            />
                        ))}
                    </div>
                )}

                {/* 設定按鈕 */}
                <div style={{ marginTop: 24, marginBottom: 80 }}>
                    <Tag
                        icon={<SettingOutlined />}
                        onClick={() => navigate('/settings')}
                        style={{
                            cursor: 'pointer',
                            padding: '8px 16px',
                            borderRadius: 20,
                            background: '#2d2d2d',
                            border: 'none',
                            color: '#888',
                        }}
                    >
                        酒窖設定
                    </Tag>
                </div>

                {/* 版本資訊 */}
                <VersionFooter />

                {/* 浮動加號按鈕 */}
                <FloatAddButton onClick={() => navigate('/add')} />
            </Content>
        </Layout>
    );
}

export default WineHome;
