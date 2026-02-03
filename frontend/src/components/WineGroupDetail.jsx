/**
 * WineGroupDetail.jsx
 * 
 * 酒款群組詳情頁 - 顯示同款酒的所有瓶子
 * 每個瓶子可以單獨查看和編輯
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Layout,
    Card,
    List,
    Tag,
    Button,
    Typography,
    Space,
    message,
    Select,
    Divider,
    Image
} from 'antd';
import {
    ArrowLeftOutlined,
    EyeOutlined,
    EditOutlined,
    GiftOutlined,
    ShopOutlined,
    InboxOutlined,
    UserOutlined
} from '@ant-design/icons';
import { getFoodItems, updateWineDisposition } from '../services/api';
import WineDetailModal from './WineDetailModal';

const { Content } = Layout;
const { Title, Text } = Typography;

const dispositionIcons = {
    personal: <UserOutlined />,
    gift: <GiftOutlined />,
    sale: <ShopOutlined />,
    collection: <InboxOutlined />
};

const dispositionLabels = {
    personal: '自飲',
    gift: '送禮',
    sale: '待售',
    collection: '收藏'
};

const dispositionColors = {
    personal: 'blue',
    gift: 'gold',
    sale: 'green',
    collection: 'purple'
};

function WineGroupDetail() {
    const { brand, name, vintage } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [bottles, setBottles] = useState([]);
    const [selectedBottle, setSelectedBottle] = useState(null);
    const [modalVisible, setModalVisible] = useState(false);

    useEffect(() => {
        fetchBottles();
    }, [brand, name, vintage]);

    const fetchBottles = async () => {
        try {
            setLoading(true);
            const items = await getFoodItems();

            // 篩選出相同的酒款
            const filtered = items.filter(item =>
                item.brand === decodeURIComponent(brand) &&
                item.name === decodeURIComponent(name) &&
                (!vintage || item.vintage === parseInt(vintage))
            );

            setBottles(filtered);
        } catch (error) {
            message.error('載入失敗');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDispositionChange = async (bottleId, newDisposition) => {
        try {
            await updateWineDisposition(bottleId, newDisposition);
            message.success('已更新用途');
            fetchBottles();
        } catch (error) {
            message.error('更新失敗');
        }
    };

    const handleViewBottle = (bottle) => {
        setSelectedBottle(bottle);
        setModalVisible(true);
    };

    if (loading) {
        return (
            <Layout style={{ minHeight: '100vh', background: '#2d2d2d' }}>
                <Content style={{ padding: 24 }}>
                    <Text style={{ color: '#fff' }}>載入中...</Text>
                </Content>
            </Layout>
        );
    }

    const firstBottle = bottles[0];
    if (!firstBottle) {
        return (
            <Layout style={{ minHeight: '100vh', background: '#2d2d2d' }}>
                <Content style={{ padding: 24 }}>
                    <Button
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate(-1)}
                        style={{ marginBottom: 16 }}
                    >
                        返回
                    </Button>
                    <Text style={{ color: '#fff' }}>找不到酒款</Text>
                </Content>
            </Layout>
        );
    }

    return (
        <Layout style={{ minHeight: '100vh', background: '#2d2d2d' }}>
            <Content style={{ padding: 24, maxWidth: 800, margin: '0 auto', width: '100%' }}>
                {/* 返回按鈕 */}
                <Button
                    icon={<ArrowLeftOutlined />}
                    onClick={() => navigate(-1)}
                    style={{
                        marginBottom: 24,
                        background: '#3d3d3d',
                        borderColor: '#555',
                        color: '#f5f5f5'
                    }}
                >
                    返回
                </Button>

                {/* 酒款資訊卡片 */}
                <Card
                    style={{
                        background: '#3d3d3d',
                        borderColor: '#555',
                        marginBottom: 24
                    }}
                    bodyStyle={{ padding: 24 }}
                >
                    <div style={{ display: 'flex', gap: 24 }}>
                        {/* 酒款圖片 */}
                        {firstBottle.image_url && (
                            <Image
                                src={firstBottle.image_url}
                                alt={firstBottle.name}
                                loading="lazy"
                                style={{
                                    width: 120,
                                    height: 120,
                                    objectFit: 'cover',
                                    borderRadius: 8
                                }}
                            />
                        )}

                        {/* 酒款資訊 */}
                        <div style={{ flex: 1 }}>
                            <Title level={3} style={{ color: '#fff', marginBottom: 8 }}>
                                {firstBottle.name}
                            </Title>
                            <Space wrap>
                                <Tag color="gold">{firstBottle.wine_type}</Tag>
                                {firstBottle.vintage && <Tag>{firstBottle.vintage}</Tag>}
                                {firstBottle.brand && <Tag color="blue">{firstBottle.brand}</Tag>}
                                {firstBottle.region && <Tag>{firstBottle.region}</Tag>}
                            </Space>
                            <Divider style={{ borderColor: '#555', margin: '16px 0' }} />
                            <Text style={{ color: '#888', fontSize: 16 }}>
                                總數量：<span style={{ color: '#c9a227', fontSize: 20, fontWeight: 'bold' }}>{bottles.length}</span> 瓶
                            </Text>
                        </div>
                    </div>
                </Card>

                {/* 瓶子列表 */}
                <Card
                    title={<span style={{ color: '#fff' }}>瓶子清單</span>}
                    style={{
                        background: '#3d3d3d',
                        borderColor: '#555'
                    }}
                    bodyStyle={{ padding: 0 }}
                >
                    <List
                        dataSource={bottles}
                        renderItem={(bottle, index) => (
                            <List.Item
                                style={{
                                    padding: '16px 24px',
                                    borderBottom: '1px solid #555',
                                    background: index % 2 === 0 ? '#3d3d3d' : '#353535'
                                }}
                                actions={[
                                    <Button
                                        key="view"
                                        type="text"
                                        icon={<EyeOutlined />}
                                        onClick={() => handleViewBottle(bottle)}
                                        style={{ color: '#c9a227' }}
                                    >
                                        查看
                                    </Button>,
                                    <Button
                                        key="edit"
                                        type="text"
                                        icon={<EditOutlined />}
                                        onClick={() => navigate(`/edit/${bottle.id}`)}
                                        style={{ color: '#888' }}
                                    >
                                        編輯
                                    </Button>
                                ]}
                            >
                                <List.Item.Meta
                                    avatar={
                                        <div style={{
                                            width: 40,
                                            height: 40,
                                            borderRadius: '50%',
                                            background: '#c9a227',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: '#2d2d2d',
                                            fontWeight: 'bold',
                                            fontSize: 16
                                        }}>
                                            #{index + 1}
                                        </div>
                                    }
                                    title={
                                        <Space>
                                            <Text style={{ color: '#f5f5f5' }}>
                                                瓶子 #{index + 1}
                                            </Text>
                                            <Tag
                                                color={dispositionColors[bottle.disposition || 'personal']}
                                                icon={dispositionIcons[bottle.disposition || 'personal']}
                                            >
                                                {dispositionLabels[bottle.disposition || 'personal']}
                                            </Tag>
                                            {bottle.bottle_status === 'opened' && (
                                                <Tag color="orange">已開瓶</Tag>
                                            )}
                                        </Space>
                                    }
                                    description={
                                        <div style={{ marginTop: 8 }}>
                                            <Text style={{ color: '#888', marginRight: 16 }}>
                                                用途：
                                            </Text>
                                            <Select
                                                value={bottle.disposition || 'personal'}
                                                onChange={(value) => handleDispositionChange(bottle.id, value)}
                                                style={{ width: 120 }}
                                                size="small"
                                                options={[
                                                    { value: 'personal', label: '🍷 自飲' },
                                                    { value: 'gift', label: '🎁 送禮' },
                                                    { value: 'collection', label: '📦 收藏' }
                                                ]}
                                            />
                                        </div>
                                    }
                                />
                            </List.Item>
                        )}
                    />
                </Card>
            </Content>

            {/* 詳情 Modal */}
            <WineDetailModal
                visible={modalVisible}
                wine={selectedBottle}
                onClose={() => {
                    setModalVisible(false);
                    setSelectedBottle(null);
                }}
                onUpdate={fetchBottles}
            />
        </Layout>
    );
}

export default WineGroupDetail;
