
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
    Modal,
    Skeleton,
    Avatar
} from 'antd';
import {
    CalendarOutlined,
    EnvironmentOutlined,
    CheckCircleFilled,
    GoogleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { joinInvitation } from '../services/api';
import apiClient from '../services/api';
import { useMode } from '../contexts/ModeContext';

const { Content } = Layout;
const { Title, Text } = Typography;

// API Base URL - 現在使用統一的 apiClient

const InvitationDetail = () => {
    const { id } = useParams();
    const { theme } = useMode();
    const [invitation, setInvitation] = useState(null);
    const [wines, setWines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [sending, setSending] = useState(false);
    const [attendees, setAttendees] = useState([]);
    const [hasRSVPd, setHasRSVPd] = useState(false);

    useEffect(() => {
        const fetchInvitation = async () => {
            try {
                // Fetch invitation details
                // Use fetch directly to bypass auth token requirement for guests
                // apiClient 的攔截器已經返回 response.data
                const data = await apiClient.get(`/invitations/${id}`);
                
                if (!data) {
                    throw new Error('API 返回空數據');
                }
                
                setInvitation(data);

                if (data.wine_details && data.wine_details.length > 0) {
                    setWines(data.wine_details);
                } else {
                    setWines([]);
                }

                // Set attendees from API response
                if (data.attendees && data.attendees.length > 0) {
                    setAttendees(data.attendees);
                }

                // Check localStorage for existing RSVP
                if (localStorage.getItem(`rsvp_${id}`) === 'true') {
                    setHasRSVPd(true);
                }

            } catch (err) {
                console.error(err);
                // 檢查是否為模擬ID（13位數字時間戳）
                const isSimulatedId = /^\d{13}$/.test(id);
                if (isSimulatedId) {
                    setError('這是測試邀請，詳情頁面暫不可用。邀請發送功能正常！');
                } else {
                    setError(err.message);
                }
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
            const context = liff.getContext();
            const rsvpMessage = [{ type: 'text', text: `我要參加「${invitation.title}」 +1 🍷` }];
            const hasChatContext = context && (context.type === 'utou' || context.type === 'group' || context.type === 'room' || context.type === 'square_chat');

            if (hasChatContext) {
                // Opened from a LINE chat — sendMessages delivers to that chat
                await liff.sendMessages(rsvpMessage);

                // Save to backend
                try {
                    const profile = await liff.getProfile();
                    const result = await joinInvitation(id, {
                        line_user_id: profile.userId,
                        name: profile.displayName,
                        avatar_url: profile.pictureUrl
                    });
                    setAttendees(prev => {
                        if (prev.some(a => a.line_user_id === result.line_user_id)) return prev;
                        return [...prev, result];
                    });
                    // Save to localStorage
                    localStorage.setItem(`rsvp_${id}`, 'true');
                    setHasRSVPd(true);
                } catch (joinErr) {
                    console.warn('Failed to save attendee:', joinErr);
                }

                Modal.success({
                    title: '報名成功！',
                    content: '已在聊天室發送 +1 訊息。要順便加入行事曆嗎？',
                    okText: '好的，加入行事曆',
                    closable: true,
                    onOk: handleAddToCalendar,
                    styles: {
                        body: theme === 'chill' ? { color: 'white' } : {},
                        header: theme === 'chill' ? { color: 'white' } : {}
                    }
                });
            } else if (liff.isApiAvailable('shareTargetPicker')) {
                // No chat context — let user pick a chat to send to
                const res = await liff.shareTargetPicker(rsvpMessage);
                if (res && res.status === 'success') {
                    // Save to backend
                    try {
                        const profile = await liff.getProfile();
                        const result = await joinInvitation(id, {
                            line_user_id: profile.userId,
                            name: profile.displayName,
                            avatar_url: profile.pictureUrl
                        });
                        setAttendees(prev => {
                            if (prev.some(a => a.line_user_id === result.line_user_id)) return prev;
                            return [...prev, result];
                        });
                        // Save to localStorage
                        localStorage.setItem(`rsvp_${id}`, 'true');
                        setHasRSVPd(true);
                    } catch (joinErr) {
                        console.warn('Failed to save attendee:', joinErr);
                    }

                    Modal.success({
                        title: '報名成功！',
                        content: '已發送 +1 訊息。要順便加入行事曆嗎？',
                        okText: '好的，加入行事曆',
                        closable: true,
                        onOk: handleAddToCalendar,
                        styles: {
                            body: theme === 'chill' ? { color: 'white' } : {},
                            header: theme === 'chill' ? { color: 'white' } : {}
                        }
                    });
                } else {
                    message.info('已取消發送');
                }
            } else {
                message.warning('請從 LINE 聊天室中開啟此連結，才能使用報名功能');
            }

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

    const handleNavigateToLocation = () => {
        if (!invitation.location) return;

        // 優先使用用戶當前位置進行導航
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // 有用戶位置 - 使用導航模式
                    const userLat = position.coords.latitude;
                    const userLng = position.coords.longitude;
                    const destination = encodeURIComponent(invitation.location);
                    
                    // 使用 Google Maps 導航 URL 格式
                    const navigationUrl = `https://www.google.com/maps/dir/${userLat},${userLng}/${destination}`;
                    window.open(navigationUrl, '_blank');
                    
                    message.success('正在開啟 Google Maps 導航...');
                },
                (error) => {
                    // 無法獲取用戶位置 - fallback 到搜尋模式
                    console.warn('無法獲取用戶位置:', error);
                    const searchUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(invitation.location)}`;
                    window.open(searchUrl, '_blank');
                    
                    message.info('正在開啟 Google Maps 搜尋...');
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 300000 // 5分鐘
                }
            );
        } else {
            // 瀏覽器不支援地理位置 - 使用搜尋模式
            const searchUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(invitation.location)}`;
            window.open(searchUrl, '_blank');
            
            message.info('正在開啟 Google Maps 搜尋...');
        }
    };

    if (loading) {
        return (
            <Layout style={{ minHeight: '100vh', background: theme.background }}>
                {/* Hero Skeleton */}
                <div style={{ height: 240, background: theme.card, animation: 'pulse 1.5s infinite ease-in-out' }}>
                    <Skeleton.Image active style={{ width: '100%', height: '100%' }} />
                </div>
                <Content style={{ padding: '24px', maxWidth: 600, margin: '0 auto', width: '100%' }}>
                    <Card style={{ background: theme.card, border: 'none', borderRadius: 12, marginBottom: 24 }} styles={{ body: { padding: 20 } }}>
                        <Skeleton active paragraph={{ rows: 3 }} />
                    </Card>
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        {[1, 2, 3].map(i => (
                            <Card key={i} style={{ background: theme.card, border: 'none', borderRadius: 12 }} styles={{ body: { padding: 12 } }}>
                                <Skeleton active avatar paragraph={{ rows: 1 }} />
                            </Card>
                        ))}
                    </Space>
                </Content>
            </Layout>
        );
    }

    if (error || !invitation) {
        return (
            <div style={{ minHeight: '100vh', background: theme.background, padding: 40, textAlign: 'center', color: '#fff' }}>
                <Title level={4} style={{ color: '#ff4d4f' }}>{error || '無法讀取邀請函'}</Title>
            </div>
        );
    }

    const isEventEnded = dayjs(invitation.event_time).isBefore(dayjs());

    return (
        <Layout style={{ minHeight: '100vh', background: theme.background }}>
            {/* Event Ended Banner */}
            {isEventEnded && (
                <div style={{ background: '#444', textAlign: 'center', padding: '10px 16px' }}>
                    <Text style={{ color: '#ccc', fontSize: 14 }}>此聚會已結束</Text>
                </div>
            )}

            {/* Hero Section */}
            <div style={{ position: 'relative', height: 240 }}>
                <img
                    src={invitation.theme_image_url || "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"}
                    alt="Cover"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', filter: isEventEnded ? 'brightness(0.35)' : 'brightness(0.6)' }}
                    loading="lazy"
                />
                {isEventEnded && (
                    <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.3)' }} />
                )}
                <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', padding: '24px', background: `linear-gradient(to top, ${theme.background}, transparent)` }}>
                    <Title level={2} style={{ color: '#c9a227', margin: 0, textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>
                        {invitation.title}
                    </Title>
                </div>
            </div>

            <Content style={{ padding: '24px', maxWidth: 600, margin: '0 auto', width: '100%' }}>
                {/* Info Card */}
                <Card style={{ background: theme.card, border: 'none', borderRadius: 12, marginBottom: 24 }} styles={{ body: { padding: 20 } }}>
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

                        <div 
                            style={{ 
                                display: 'flex', 
                                gap: 12, 
                                cursor: invitation.location ? 'pointer' : 'default',
                                padding: '8px',
                                borderRadius: '8px',
                                transition: 'background-color 0.2s'
                            }}
                            onClick={invitation.location ? () => handleNavigateToLocation() : undefined}
                            onMouseEnter={(e) => invitation.location && (e.target.style.backgroundColor = '#444')}
                            onMouseLeave={(e) => invitation.location && (e.target.style.backgroundColor = 'transparent')}
                        >
                            <EnvironmentOutlined style={{ fontSize: 20, color: '#c9a227', marginTop: 4 }} />
                            <div>
                                <Text 
                                    strong 
                                    style={{ 
                                        color: '#fff', 
                                        fontSize: 16, 
                                        display: 'block',
                                        textDecoration: invitation.location ? 'underline' : 'none'
                                    }}
                                >
                                    {invitation.location || "地點待定"}
                                </Text>
                                {invitation.location && (
                                    <Text style={{ color: '#888', fontSize: 12 }}>
                                        點擊開啟 Google Maps
                                    </Text>
                                )}
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
                        <Card key={wine.id} style={{ background: theme.card, border: 'none', borderRadius: 12 }} styles={{ body: { padding: 12 } }}>
                            <Row gutter={16} align="middle">
                                <Col flex="80px">
                                    <div style={{ width: 80, height: 80, background: '#111', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <img
                                            src={wine.image_url || 'https://via.placeholder.com/80'}
                                            alt={wine.name}
                                            style={{ maxHeight: '90%', maxWidth: '90%', objectFit: 'contain' }}
                                            loading="lazy"
                                        />
                                    </div>
                                </Col>
                                <Col flex="auto">
                                    <Text strong style={{ color: '#fff', fontSize: 16, display: 'block', marginBottom: 4 }}>
                                        {wine.name}
                                    </Text>
                                    <Space>
                                        <Tag color="gold">{wine.wine_type}</Tag>
                                        {wine.vintage && (
                                            <Tag style={{ background: '#444', border: 'none', color: '#ccc' }}>
                                                {wine.vintage}
                                            </Tag>
                                        )}
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

                {/* Attendees Avatar List */}
                {attendees.length > 0 && (
                    <>
                        <Divider style={{ borderColor: '#333', color: '#c9a227' }}>已報名 ({attendees.length})</Divider>
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
                            <Avatar.Group
                                maxCount={10}
                                size="large"
                                maxStyle={{ color: theme.primary, backgroundColor: theme.card, border: `2px solid ${theme.primary}` }}
                            >
                                {attendees.map((att, index) => (
                                    <Avatar
                                        key={att.line_user_id || index}
                                        src={att.avatar_url}
                                        style={{ border: '2px solid #c9a227' }}
                                    >
                                        {att.name?.charAt(0)}
                                    </Avatar>
                                ))}
                            </Avatar.Group>
                        </div>
                    </>
                )}

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
                            loading={!isEventEnded && !hasRSVPd && sending}
                            disabled={isEventEnded || hasRSVPd}
                            icon={<CheckCircleFilled />}
                            style={{
                                height: 50,
                                borderRadius: 25,
                                background: isEventEnded ? '#555' : hasRSVPd ? '#2d5016' : '#c9a227',
                                borderColor: isEventEnded ? '#555' : hasRSVPd ? '#3d7a1c' : '#c9a227',
                                color: isEventEnded ? '#999' : hasRSVPd ? '#8fbc8f' : '#000',
                                fontWeight: 'bold'
                            }}
                            onClick={(isEventEnded || hasRSVPd) ? undefined : handleRSVP}
                        >
                            {isEventEnded ? '聚會已結束' : hasRSVPd ? '✓ 已報名' : '我會參加'}
                        </Button>
                    </Col>
                </Row>

            </Content>
        </Layout>
    );
};

export default InvitationDetail;
