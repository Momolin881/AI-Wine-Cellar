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

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal, Button, Tag, Typography, Slider, Row, Col, Divider, message } from 'antd';
import { CloseOutlined, CalendarOutlined, EditOutlined } from '@ant-design/icons';
import confetti from 'canvas-confetti';
import '../styles/WineDetailModal.css';

const { Title, Text } = Typography;

// Play a simple "pop" sound using Web Audio API
const playPopSound = () => {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // Create a short "pop" sound
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.setValueAtTime(150, audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

        gainNode.gain.setValueAtTime(0.8, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);

        // Create a "fizz" noise for champagne effect
        const bufferSize = audioContext.sampleRate * 0.3;
        const noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }

        const noiseSource = audioContext.createBufferSource();
        const noiseGain = audioContext.createGain();
        const noiseFilter = audioContext.createBiquadFilter();

        noiseSource.buffer = noiseBuffer;
        noiseFilter.type = 'highpass';
        noiseFilter.frequency.value = 3000;

        noiseSource.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(audioContext.destination);

        noiseGain.gain.setValueAtTime(0.3, audioContext.currentTime + 0.05);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);

        noiseSource.start(audioContext.currentTime + 0.05);
        noiseSource.stop(audioContext.currentTime + 0.4);

    } catch (e) {
        console.warn("Audio play failed:", e);
    }
};

function WineDetailModal({ visible, wine, onClose, onUpdate }) {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    if (!wine) return null;

    const handleOpenBottle = async () => {
        try {
            setLoading(true);

            // 1. Play Pop Sound
            playPopSound();

            // 2. Confetti Animation - use higher zIndex to appear above modal
            // Fire multiple bursts for more dramatic effect
            const colors = ['#c9a227', '#ffd700', '#ffffff', '#e5e5e5'];

            // Create custom canvas with high z-index
            const myCanvas = document.createElement('canvas');
            myCanvas.style.position = 'fixed';
            myCanvas.style.top = '0';
            myCanvas.style.left = '0';
            myCanvas.style.width = '100vw';
            myCanvas.style.height = '100vh';
            myCanvas.style.pointerEvents = 'none';
            myCanvas.style.zIndex = '99999'; // Above modal
            document.body.appendChild(myCanvas);

            const myConfetti = confetti.create(myCanvas, { resize: true });

            // Fire confetti burst
            myConfetti({
                particleCount: 150,
                spread: 100,
                origin: { y: 0.5, x: 0.5 },
                colors: colors,
                startVelocity: 45,
                gravity: 1,
                ticks: 300,
            });

            // Second burst after short delay
            setTimeout(() => {
                myConfetti({
                    particleCount: 80,
                    spread: 60,
                    origin: { y: 0.6, x: 0.3 },
                    colors: colors,
                });
                myConfetti({
                    particleCount: 80,
                    spread: 60,
                    origin: { y: 0.6, x: 0.7 },
                    colors: colors,
                });
            }, 200);

            // Remove canvas after animation
            setTimeout(() => {
                document.body.removeChild(myCanvas);
            }, 4000);

            // 3. Call API
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_BASE}/api/v1/wine-items/${wine.id}/open`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('liffAccessToken') || 'dev-test-token'}`,
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

        // If empty, confirm and mark as consumed (not delete, to preserve spending history)
        if (value === 0) {
            Modal.confirm({
                title: '確定喝完了嗎？',
                content: `「${wine.name}」將標記為已喝完，並從酒窖移除`,
                okText: '確定，已喝完',
                cancelText: '取消',
                okButtonProps: { style: { background: '#c9a227', borderColor: '#c9a227' } },
                onOk: async () => {
                    try {
                        const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                        const res = await fetch(`${API_BASE}/api/v1/wine-items/${wine.id}/change-status?new_status=consumed`, {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${localStorage.getItem('liffAccessToken') || 'dev-test-token'}`,
                                'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo'
                            }
                        });
                        if (res.ok) {
                            message.success('🍾 乾杯！已記錄為喝完');
                            onClose();
                            // Trigger a refresh by calling onUpdate with a deleted flag (to remove from active list)
                            onUpdate({ ...wine, _deleted: true });
                        } else {
                            message.error('操作失敗，請稍後再試');
                        }
                    } catch (error) {
                        console.error("Change status error:", error);
                        message.error('發生錯誤');
                    }
                }
            });
            return;
        }

        try {
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            await fetch(`${API_BASE}/api/v1/wine-items/${wine.id}/update-remaining?remaining=${amount}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('liffAccessToken') || 'dev-test-token'}`,
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
            styles={{
                body: { padding: 0, borderRadius: 16, overflow: 'hidden', background: '#2d2d2d' },
                mask: { backdropFilter: 'blur(5px)' }
            }}
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
                            styles={{
                                rail: { backgroundColor: '#444' },
                                track: { backgroundColor: '#c9a227' },
                                handle: { borderColor: '#c9a227', backgroundColor: '#c9a227' }
                            }}
                        />
                    </div>
                )}

                {/* 編輯按鈕 */}
                <Divider style={{ borderColor: '#444', margin: '24px 0 16px' }} />
                <Button
                    icon={<EditOutlined />}
                    block
                    onClick={() => {
                        onClose();
                        navigate(`/edit/${wine.id}`);
                    }}
                    style={{
                        background: '#3d3d3d',
                        borderColor: '#555',
                        color: '#f5f5f5',
                        height: 44,
                        borderRadius: 22,
                    }}
                >
                    編輯酒款資料
                </Button>
            </div>
        </Modal>
    );
}

export default WineDetailModal;
