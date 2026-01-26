
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import liff from '@line/liff';
import {
    Layout,
    Typography,
    Form,
    Input,
    DatePicker,
    Button,
    Card,
    Row,
    Col,
    Checkbox,
    message,
    Spin
} from 'antd';
import {
    CalendarOutlined,
    EnvironmentOutlined,
    UserOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CreateInvitation = () => {
    const navigate = useNavigate();
    const [form] = Form.useForm();
    const [availableWines, setAvailableWines] = useState([]);
    const [selectedWines, setSelectedWines] = useState([]);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Initial values
    const initialValues = {
        title: '',
        event_time: dayjs(),
        location: '',
        description: '',
    };

    // Fetch wines from backend
    useEffect(() => {
        const fetchWines = async () => {
            try {
                setLoading(true);
                // Call actual API
                const response = await fetch(`${API_BASE_URL}/api/v1/wine-items?status=active`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('liffAccessToken') || ''}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    setAvailableWines(Array.isArray(data) ? data : []);
                } else {
                    // Fallback mock data if API fails or auth issues
                    console.warn("API fetch failed, using mock data");
                    const mockWines = [
                        { id: 1, name: 'Chateau Margaux 2015', image_url: 'https://via.placeholder.com/150' },
                        { id: 2, name: 'Opus One 2018', image_url: 'https://via.placeholder.com/150' },
                        { id: 3, name: 'Penfolds Grange 2016', image_url: 'https://via.placeholder.com/150' },
                    ];
                    setAvailableWines(mockWines);
                }
            } catch (err) {
                console.error("Failed to fetch wines", err);
                message.error("無法載入酒款資料");
            } finally {
                setLoading(false);
            }
        };
        fetchWines();
    }, []);

    const handleWineToggle = (wineId) => {
        setSelectedWines(prev => {
            if (prev.includes(wineId)) {
                return prev.filter(id => id !== wineId);
            } else {
                return [...prev, wineId];
            }
        });
    };

    const handleFinish = async (values) => {
        if (selectedWines.length === 0 && !confirm("您沒有選擇任何酒款，確定要繼續嗎？")) {
            return;
        }

        setSubmitting(true);
        try {
            // 1. Call Backend API to create invitation
            const payload = {
                title: values.title,
                event_time: values.event_time.toISOString(), // Antd DatePicker returns dayjs object
                location: values.location,
                description: values.description,
                wine_ids: selectedWines,
                theme_image_url: 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
            };

            const response = await fetch(`${API_BASE_URL}/api/v1/invitations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('liffAccessToken') || ''}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('無法建立邀請');
            }

            const data = await response.json();

            // 2. Fetch generated Flex Message
            const flexRes = await fetch(`${API_BASE_URL}/api/v1/invitations/${data.id}/flex`);
            const flexMessage = await flexRes.json();

            // 3. Use LIFF shareTargetPicker to send message
            if (liff.isApiAvailable('shareTargetPicker')) {
                const res = await liff.shareTargetPicker([flexMessage]);
                if (res) {
                    message.success("邀請已成功發送！");
                    setTimeout(() => navigate('/'), 2000);
                } else {
                    message.info("已建立邀請，但未發送訊息。");
                    setTimeout(() => navigate('/'), 2000);
                }
            } else {
                // Fallback: Copy link
                message.success("建立成功！請複製連結分享");
                // navigate(`/invitation/${data.id}`);
            }

        } catch (err) {
            console.error(err);
            message.error(err.message || "發生錯誤");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Layout style={{ minHeight: '100vh', background: '#1a1a1a' }}>
            <Content style={{ padding: '24px', maxWidth: 600, margin: '0 auto' }}>
                <Title level={3} style={{ color: '#c9a227', marginBottom: 24, textAlign: 'center' }}>
                    發起品飲聚會 🥂
                </Title>

                <Form
                    form={form}
                    layout="vertical"
                    initialValues={initialValues}
                    onFinish={handleFinish}
                    style={{ color: '#fff' }}
                >
                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>聚會標題</span>}
                        name="title"
                        rules={[{ required: true, message: '請輸入標題' }]}
                    >
                        <Input
                            placeholder="例如：週末品酒會"
                            style={{ background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                        />
                    </Form.Item>

                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>時間</span>}
                        name="event_time"
                        rules={[{ required: true, message: '請選擇時間' }]}
                    >
                        <DatePicker
                            showTime
                            format="YYYY-MM-DD HH:mm"
                            style={{ width: '100%', background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                            popupStyle={{ background: '#2d2d2d' }}
                        />
                    </Form.Item>

                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>地點</span>}
                        name="location"
                    >
                        <Input
                            prefix={<EnvironmentOutlined style={{ color: '#888' }} />}
                            placeholder="輸入地點"
                            style={{ background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                        />
                    </Form.Item>

                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>備註</span>}
                        name="description"
                    >
                        <TextArea
                            rows={3}
                            placeholder="有什麼想對朋友說的..."
                            style={{ background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                        />
                    </Form.Item>

                    <Typography.Text strong style={{ color: '#c9a227', display: 'block', margin: '24px 0 12px' }}>
                        選擇今日酒單 ({selectedWines.length})
                    </Typography.Text>

                    {loading ? <Spin /> : (
                        <Row gutter={[16, 16]}>
                            {availableWines.map(wine => (
                                <Col span={12} key={wine.id}>
                                    <div
                                        onClick={() => handleWineToggle(wine.id)}
                                        style={{
                                            position: 'relative',
                                            cursor: 'pointer',
                                            borderRadius: 8,
                                            overflow: 'hidden',
                                            border: selectedWines.includes(wine.id) ? '2px solid #c9a227' : '2px solid transparent'
                                        }}
                                    >
                                        <div style={{ height: 120, background: '#2d2d2d', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <img
                                                src={wine.image_url || 'https://via.placeholder.com/100'}
                                                alt={wine.name}
                                                style={{ maxHeight: '90%', maxWidth: '90%', objectFit: 'contain' }}
                                            />
                                        </div>
                                        <div style={{ padding: 8, background: '#333' }}>
                                            <Text ellipsis style={{ color: '#fff', width: '100%', display: 'block' }}>{wine.name}</Text>
                                        </div>
                                        {selectedWines.includes(wine.id) && (
                                            <div style={{ position: 'absolute', top: 5, right: 5, background: '#c9a227', borderRadius: '50%', width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                ✓
                                            </div>
                                        )}
                                    </div>
                                </Col>
                            ))}
                            {availableWines.length === 0 && (
                                <Col span={24}>
                                    <div style={{ padding: 20, textAlign: 'center', color: '#666', background: '#2d2d2d', borderRadius: 8 }}>
                                        沒有可用的酒款 (請先在「我的酒窖」新增)
                                    </div>
                                </Col>
                            )}
                        </Row>
                    )}

                    <Button
                        type="primary"
                        htmlType="submit"
                        loading={submitting}
                        block
                        size="large"
                        style={{ marginTop: 40, height: 50, borderRadius: 25, background: '#c9a227', borderColor: '#c9a227', color: '#000', fontWeight: 'bold' }}
                    >
                        建立邀請並發送
                    </Button>
                </Form>
            </Content>
        </Layout>
    );
};

export default CreateInvitation;
