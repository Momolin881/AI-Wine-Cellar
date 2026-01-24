/**
 * WineDetailModal.jsx
 * 
 * Immersive detailed view for wine items.
 * Features:
 * - Large visual display
 * - "Open Bottle" interactive button with sound & animation
 * - Drink By countdown
 * - Remaining amount slider
 */

import { useState, useEffect, useRef } from 'react';
import { Modal, Button, Tag, Typography, Slider, Row, Col, Divider, message } from 'antd';
import { CloseOutlined, SoundOutlined, CalendarOutlined } from '@ant-design/icons';
import confetti from 'canvas-confetti'; // Assuming we can install this or use a CDN/local fallback
import '../styles/WineDetailModal.css';

const { Title, Text, Paragraph } = Typography;

// Sound effect (Base64 or URL) - Using a placeholder URL for now
const CORK_POP_SOUND = "https://assets.mixkit.co/sfx/preview/mixkit-cork-pop-glass-clink-1688.mp3";

function WineDetailModal({ visible, wine, onClose, onUpdate }) {
    if (!wine) return null;

    const [loading, setLoading] = useState(false);
    const audioRef = useRef(new Audio(CORK_POP_SOUND));

    const handleOpenBottle = async () => {
        try {
            setLoading(true);

            // 1. Play Sound
            audioRef.current.play().catch(e => console.error("Audio play failed", e));

            // 2. Confetti Animation
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#c9a227', '#ffffff', '#e5e5e5'] // Gold and White
            });

            // 3. Call API
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_BASE}/api/v1/wine-items/${wine.id}/open`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('liffAccessToken')}`, // Assuming token logic
                    'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo'
                }
            });

            if (res.ok) {
                const updatedWine = await res.json();
                message.success("🍾 開瓶慶祝！請享受您的美酒！");
                onUpdate(updatedWine);
            } else {
                message.error("開瓶失敗，請稍後再試");
            }

        } catch (error) {
            console.error("Open bottle error:", error);
            message.error("發生錯誤");
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateRemaining = async (value) => {
        // Map slider value (0, 25, 50, 75, 100) to API strings
        const map = {
            100: 'full',
            75: '3/4',
            50: '1/2',
            25: '1/4',
            0: 'empty'
        };
        const amount = map[value];
        if (!amount) return;

        try {
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            await fetch(`${API_BASE}/api/v1/wine-items/${wine.id}/update-remaining?remaining=${amount}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo'
                }
            });
            onUpdate({ ...wine, remaining_amount: amount });
        } catch (error) {
            console.error("Update remaining error:", error);
        }
    };

    // Helper to convert API string to slider value
    const getSliderValue = (amount) => {
        const map = {
            'full': 100,
            '3/4': 75,
            '1/2': 50,
            '1/4': 25,
            'empty': 0
        };
        return map[amount] || 100;
    };

    const isOpened = wine.bottle_status === 'opened';

    return (
        <Modal
            open={visible}
            onCancel={onClose}
            footer={null}
            closable={false}
            centered
            width={360}
            bodyStyle={{ padding: 0, borderRadius: 16, overflow: 'hidden', background: '#2d2d2d' }}
            maskStyle={{ backdropFilter: 'blur(5px)' }}
        >
            {/* Header Image */}
            <div style={{ position: 'relative', height: 280, width: '100%', background: '#000' }}>
                <img
                    src={wine.image_url}
                    alt={wine.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }}
                />
                <Button
                    type="text"
                    icon={<CloseOutlined style={{ color: '#fff', fontSize: 20 }} />}
                    style={{ position: 'absolute', top: 16, right: 16, zIndex: 10 }}
                    onClick={onClose}
                />
                <div style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    background: 'linear-gradient(to top, #2d2d2d, transparent)',
                    height: 80
                }} />
            </div>

            {/* Content */}
            <div style={{ padding: '0 24px 24px 24px' }}>
                <Title level={3} style={{ color: '#fff', margin: 0 }}>{wine.name}</Title>
                <div style={{ marginTop: 8, marginBottom: 16 }}>
                    <Tag color="gold">{wine.wine_type}</Tag>
                    {wine.vintage && <Tag color="default">{wine.vintage}</Tag>}
                    {wine.region && <Text style={{ color: '#888', marginLeft: 8 }}>{wine.region}</Text>}
                </div>

                <Divider style={{ borderColor: '#444' }} />

                {/* Preservation Type Info */}
                <div style={{ marginBottom: 16 }}>
                    <Text style={{ color: '#888' }}>類型：</Text>
                    <Text style={{ color: '#f5f5f5' }}>
                        {wine.preservation_type === 'aging' ? '陳年型 (適合慢飲)' : '即飲型 (開瓶後盡快)'}
                    </Text>
                </div>

                {/* Open/Status Section */}
                {!isOpened ? (
                    <div style={{ textAlign: 'center', marginTop: 32, marginBottom: 16 }}>
                        <Button
                            type="primary"
                            size="large"
                            loading={loading}
                            onClick={handleOpenBottle}
                            style={{
                                background: 'linear-gradient(45deg, #c9a227, #eebf38)',
                                border: 'none',
                                height: 56,
                                width: '100%',
                                borderRadius: 28,
                                fontSize: 18,
                                fontWeight: 'bold',
                                color: '#000',
                                boxShadow: '0 4px 15px rgba(201, 162, 39, 0.4)'
                            }}
                        >
                            🍾 開瓶慶祝
                        </Button>
                        <Text style={{ display: 'block', marginTop: 12, color: '#666', fontSize: 12 }}>
                            點擊即刻享受，並開始適飲期計時
                        </Text>
                    </div>
                ) : (
                    <div style={{ marginTop: 20 }}>
                        <div style={{
                            background: 'rgba(201, 162, 39, 0.1)',
                            borderRadius: 12,
                            padding: 16,
                            marginBottom: 24,
                            border: '1px solid rgba(201, 162, 39, 0.3)'
                        }}>
                            <Row align="middle" justify="space-between">
                                <Col>
                                    <Text style={{ color: '#c9a227', display: 'block' }}>最佳飲用期限</Text>
                                    <Title level={4} style={{ color: '#fff', margin: 0 }}>
                                        {wine.optimal_drinking_end ? wine.optimal_drinking_end : '計算中...'}
                                    </Title>
                                </Col>
                                <Col>
                                    <CalendarOutlined style={{ fontSize: 24, color: '#c9a227' }} />
                                </Col>
                            </Row>
                        </div>

                        <Text style={{ color: '#888' }}>剩餘量：</Text>
                        <Slider
                            marks={{ 0: '空', 25: '', 50: '半', 75: '', 100: '滿' }}
                            step={25}
                            defaultValue={getSliderValue(wine.remaining_amount)}
                            onChange={handleUpdateRemaining}
                            railStyle={{ backgroundColor: '#444' }}
                            trackStyle={{ backgroundColor: '#c9a227' }}
                            handleStyle={{ borderColor: '#c9a227', backgroundColor: '#c9a227' }}
                        />
                    </div>
                )}
            </div>
        </Modal>
    );
}

export default WineDetailModal;
