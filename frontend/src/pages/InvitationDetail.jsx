
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import liff from '@line/liff'; // Import LIFF
import {
    Layout,
    Typography,
    Card,
    Button,
    Tag,
    Spin,
    Divider,
    Space,
    Row,
    Col,
    message,
    Modal
} from 'antd';
import {
    CalendarOutlined,
    EnvironmentOutlined,
    CheckCircleFilled,
    GoogleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Content } = Layout;
const { Title, Text } = Typography;

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const InvitationDetail = () => {
    const { id } = useParams();
    const [invitation, setInvitation] = useState(null);
    const [wines, setWines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [sending, setSending] = useState(false);

    useEffect(() => {
        const fetchInvitation = async () => {
            try {
                // Fetch invitation details
                // Use fetch directly to bypass auth token requirement for guests
                const response = await fetch(`${API_BASE_URL}/api/v1/invitations/${id}`);
                if (!response.ok) {
                    throw new Error('找不到此邀請函');
                }
                const data = await response.json();
                setInvitation(data);

                // Backend now returns wine_details directly
                if (data.wine_details && data.wine_details.length > 0) {
                    setWines(data.wine_details);
                } else {
                    setWines([]);
                }

            } catch (err) {
                console.error(err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchInvitation();
        }
    }, [id]);

    const handleRSVP = async () => {
        if (!liff.isInClient()) {
            message.warning("請在 LINE App 中開啟以使用此功能");
            return;
        }

        setSending(true);
        try {
            await liff.sendMessages([
                {
                    type: 'text',
                    text: `我要參加「${invitation.title}」 +1 🍷`
                }
            ]);

            Modal.success({
                title: '報名成功！',
                content: '已在聊天室發送 +1 訊息。要順便加入行事曆嗎？',
                okText: '好的，加入行事曆',
                closable: true,
                onOk: handleAddToCalendar
            });

        } catch (err) {
            console.error('RSVP Error:', err);
            message.error("無法發送訊息，請檢查 LINE 權限或是手動回覆");
        } finally {
            setSending(false);
        }
    };

    const handleAddToCalendar = () => {
        if (!invitation) return;

        // Construct Google Calendar Link
        const startTime = dayjs(invitation.event_time).format('YYYYMMDDTHHmmss');
        const endTime = dayjs(invitation.event_time).add(3, 'hour').format('YYYYMMDDTHHmmss'); // Assume 3 hours duration
        const details = `酒單：\n${wines.map(w => `- ${w.name}`).join('\n')}\n\n備註：${invitation.description || ''}`;

        const calendarUrl = `https://www.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(invitation.title)}&dates=${startTime}/${endTime}&details=${encodeURIComponent(details)}&location=${encodeURIComponent(invitation.location || '')}`;

        window.open(calendarUrl, '_blank');
    };

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', background: '#1a1a1a', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Spin size="large" tip="Loading..." />
            </div>
        );
    }

    if (error || !invitation) {
        return (
            <div style={{ minHeight: '100vh', background: '#1a1a1a', padding: 40, textAlign: 'center', color: '#fff' }}>
                <Title level={4} style={{ color: '#ff4d4f' }}>{error || '無法讀取邀請函'}</Title>
            </div>
        );
    }

    return (
        <Layout style={{ minHeight: '100vh', background: '#1a1a1a' }}>
            {/* Hero Section */}
            <div style={{ position: 'relative', height: 240 }}>
                <img
                    src={invitation.theme_image_url || "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"}
                    alt="Cover"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.6)' }}
                />
                <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', padding: '24px', background: 'linear-gradient(to top, #1a1a1a, transparent)' }}>
                    <Title level={2} style={{ color: '#c9a227', margin: 0, textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>
                        {invitation.title}
                    </Title>
                </div>
            </div>

            <Content style={{ padding: '24px', maxWidth: 600, margin: '0 auto', width: '100%' }}>
                {/* Info Card */}
                <Card style={{ background: '#2d2d2d', border: 'none', borderRadius: 12, marginBottom: 24 }} bodyStyle={{ padding: 20 }}>
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', gap: 12 }}>
                            <CalendarOutlined style={{ fontSize: 20, color: '#c9a227', marginTop: 4 }} />
                            <div>
                                <Text strong style={{ color: '#fff', fontSize: 16, display: 'block' }}>
                                    {dayjs(invitation.event_time).format('YYYY年MM月DD日 (dddd)')}
                                </Text>
                                <Text style={{ color: '#888' }}>
                                    {dayjs(invitation.event_time).format('HH:mm')}
                                </Text>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: 12 }}>
                            <EnvironmentOutlined style={{ fontSize: 20, color: '#c9a227', marginTop: 4 }} />
                            <div>
                                <Text strong style={{ color: '#fff', fontSize: 16, display: 'block' }}>
                                    {invitation.location || "地點待定"}
                                </Text>
                            </div>
                        </div>

                        {invitation.description && (
                            <div style={{ padding: '12px', background: '#333', borderRadius: 8, marginTop: 8 }}>
                                <Text style={{ color: '#ccc' }}>{invitation.description}</Text>
                            </div>
                        )}
                    </Space>
                </Card>

                <Divider style={{ borderColor: '#333', color: '#c9a227' }}>今日酒單</Divider>

                {/* Wine List */}
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {wines.length > 0 ? wines.map(wine => (
                        <Card key={wine.id} style={{ background: '#2d2d2d', border: 'none', borderRadius: 12 }} bodyStyle={{ padding: 12 }}>
                            <Row gutter={16} align="middle">
                                <Col flex="80px">
                                    <div style={{ width: 80, height: 80, background: '#111', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <img
                                            src={wine.image_url || 'https://via.placeholder.com/80'}
                                            alt={wine.name}
                                            style={{ maxHeight: '90%', maxWidth: '90%', objectFit: 'contain' }}
                                        />
                                    </div>
                                </Col>
                                <Col flex="auto">
                                    <Text strong style={{ color: '#fff', fontSize: 16, display: 'block', marginBottom: 4 }}>
                                        {wine.name}
                                    </Text>
                                    <Space>
                                        <Tag color="gold">{wine.type}</Tag>
                                        <Tag style={{ background: '#444', border: 'none', color: '#ccc' }}>{wine.vintage || 'NV'}</Tag>
                                    </Space>
                                </Col>
                            </Row>
                        </Card>
                    )) : (
                        <div style={{ textAlign: 'center', color: '#666', padding: 20 }}>
                            <Text style={{ color: '#666' }}>本次聚會尚未指定酒款</Text>
                        </div>
                    )}
                </Space>

                {/* Actions */}
                <Row gutter={16} style={{ marginTop: 40 }}>
                    <Col span={12}>
                        <Button
                            block
                            size="large"
                            icon={<GoogleOutlined />}
                            style={{ height: 50, borderRadius: 25, background: '#333', borderColor: '#444', color: '#ccc' }}
                            onClick={handleAddToCalendar}
                        >
                            加入行事曆
                        </Button>
                    </Col>
                    <Col span={12}>
                        <Button
                            type="primary"
                            block
                            size="large"
                            loading={sending}
                            icon={<CheckCircleFilled />}
                            style={{ height: 50, borderRadius: 25, background: '#c9a227', borderColor: '#c9a227', color: '#000', fontWeight: 'bold' }}
                            onClick={handleRSVP}
                        >
                            我會參加
                        </Button>
                    </Col>
                </Row>

            </Content>
        </Layout>
    );
};

export default InvitationDetail;
