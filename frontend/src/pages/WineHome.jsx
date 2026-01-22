/**
 * 酒窖首頁 - 酒款清單
 *
 * 顯示所有酒款，支援篩選（酒類/開瓶狀態）和搜尋。
 * Neumorphism 深色主題
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Layout,
    Card,
    Button,
    Spin,
    Empty,
    message,
    Typography,
    Space,
    Input,
    Select,
    Tag,
    Statistic,
    Row,
    Col,
} from 'antd';
import {
    PlusOutlined,
    SearchOutlined,
    SettingOutlined,
    FilterOutlined,
} from '@ant-design/icons';
import { WineItemCard, VersionFooter } from '../components';

const { Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function WineHome() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [wineItems, setWineItems] = useState([]);
    const [filteredItems, setFilteredItems] = useState([]);
    const [cellars, setCellars] = useState([]);
    const [searchText, setSearchText] = useState('');
    const [wineTypeFilter, setWineTypeFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('active');

    // 統計資料
    const [stats, setStats] = useState({
        totalWines: 0,
        totalValue: 0,
        unopened: 0,
        opened: 0,
    });

    useEffect(() => {
        loadData();
    }, [statusFilter, wineTypeFilter]);

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

            // 取得酒窖列表
            const cellarsRes = await fetch(`${API_BASE}/api/v1/wine-cellars`, {
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const cellarsData = await cellarsRes.json();
            setCellars(cellarsData);

            // 取得酒款列表
            let url = `${API_BASE}/api/v1/wine-items?status=${statusFilter}`;
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
            const activeItems = itemsData.filter(i => i.status === 'active');
            setStats({
                totalWines: activeItems.length,
                totalValue: activeItems.reduce((sum, i) => sum + (i.total_value || 0), 0),
                unopened: activeItems.filter(i => i.bottle_status === 'unopened').length,
                opened: activeItems.filter(i => i.bottle_status === 'opened').length,
            });

        } catch (error) {
            console.error('載入資料失敗:', error);
            message.error('載入資料失敗');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (item) => {
        navigate(`/edit/${item.id}`);
    };

    const handleDelete = async (item) => {
        try {
            await fetch(`${API_BASE}/api/v1/wine-items/${item.id}`, {
                method: 'DELETE',
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            message.success('已刪除');
            loadData();
        } catch (error) {
            message.error('刪除失敗');
        }
    };

    const wineTypes = ['紅酒', '白酒', '氣泡酒', '香檳', '威士忌', '白蘭地', '清酒', '啤酒', '其他'];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Content style={{ padding: '16px', maxWidth: 480, margin: '0 auto' }}>
                {/* 標題 */}
                <div style={{ marginBottom: 20 }}>
                    <Title level={2} style={{ marginBottom: 4 }}>🍷 我的酒窖</Title>
                    <Text type="secondary">個人數位酒窖管理</Text>
                </div>

                {/* 統計看板 */}
                <Card className="neu-card" style={{ marginBottom: 20 }}>
                    <Row gutter={16}>
                        <Col span={6}>
                            <Statistic title="總酒款" value={stats.totalWines} suffix="款" />
                        </Col>
                        <Col span={6}>
                            <Statistic title="未開封" value={stats.unopened} suffix="瓶" />
                        </Col>
                        <Col span={6}>
                            <Statistic title="已開瓶" value={stats.opened} suffix="瓶" />
                        </Col>
                        <Col span={6}>
                            <Statistic
                                title="總價值"
                                value={stats.totalValue}
                                prefix="$"
                                precision={0}
                            />
                        </Col>
                    </Row>
                </Card>

                {/* 搜尋和篩選 */}
                <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
                    <Search
                        placeholder="搜尋酒款..."
                        allowClear
                        onSearch={setSearchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        style={{ flex: 1 }}
                    />
                    <Select
                        value={wineTypeFilter}
                        onChange={setWineTypeFilter}
                        style={{ width: 100 }}
                    >
                        <Option value="all">全部</Option>
                        {wineTypes.map(type => (
                            <Option key={type} value={type}>{type}</Option>
                        ))}
                    </Select>
                </div>

                {/* 狀態篩選 */}
                <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <Tag
                        color={statusFilter === 'active' ? 'gold' : 'default'}
                        onClick={() => setStatusFilter('active')}
                        style={{ cursor: 'pointer' }}
                    >
                        在庫
                    </Tag>
                    <Tag
                        color={statusFilter === 'sold' ? 'gold' : 'default'}
                        onClick={() => setStatusFilter('sold')}
                        style={{ cursor: 'pointer' }}
                    >
                        已售出
                    </Tag>
                    <Tag
                        color={statusFilter === 'gifted' ? 'gold' : 'default'}
                        onClick={() => setStatusFilter('gifted')}
                        style={{ cursor: 'pointer' }}
                    >
                        已送禮
                    </Tag>
                    <Tag
                        color={statusFilter === 'consumed' ? 'gold' : 'default'}
                        onClick={() => setStatusFilter('consumed')}
                        style={{ cursor: 'pointer' }}
                    >
                        已喝完
                    </Tag>
                </div>

                {/* 酒款列表 */}
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <Spin size="large" tip="載入中..." />
                    </div>
                ) : filteredItems.length === 0 ? (
                    <Empty
                        description={
                            wineItems.length === 0
                                ? "還沒有酒款，新增你的第一支酒吧！"
                                : "沒有符合條件的酒款"
                        }
                    >
                        {wineItems.length === 0 && (
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                onClick={() => navigate('/add')}
                            >
                                新增酒款
                            </Button>
                        )}
                    </Empty>
                ) : (
                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                        {filteredItems.map((item) => (
                            <WineItemCard
                                key={item.id}
                                item={item}
                                onEdit={() => handleEdit(item)}
                                onDelete={() => handleDelete(item)}
                            />
                        ))}
                    </Space>
                )}

                {/* 功能按鈕 */}
                <div style={{ marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <Button
                        icon={<SettingOutlined />}
                        onClick={() => navigate('/settings')}
                    >
                        酒窖設定
                    </Button>
                </div>

                {/* 版本資訊 */}
                <VersionFooter />

                {/* 新增按鈕 */}
                <Button
                    type="primary"
                    shape="circle"
                    icon={<PlusOutlined />}
                    size="large"
                    onClick={() => navigate('/add')}
                    style={{
                        position: 'fixed',
                        bottom: 80,
                        right: 20,
                        width: 60,
                        height: 60,
                        boxShadow: '5px 5px 10px #1d1d1d, -5px -5px 10px #3d3d3d',
                    }}
                />
            </Content>
        </Layout>
    );
}

export default WineHome;
