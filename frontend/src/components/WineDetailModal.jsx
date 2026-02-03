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

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal, Button, Tag, Typography, Slider, Row, Col, Divider, message, Select, InputNumber, Space } from 'antd';
import { CloseOutlined, CalendarOutlined, EditOutlined, ScissorOutlined } from '@ant-design/icons';
import confetti from 'canvas-confetti';
import apiClient, { splitWineItem, updateWineDisposition } from '../services/api';
import '../styles/WineDetailModal.css';

const { Title, Text } = Typography;

// Play a simple "pop" sound using Web Audio API
const playPopSound = () => {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const t = audioContext.currentTime;

        // 模擬軟木塞彈出的聲音：短促的噪聲 + 低頻衝擊
        const noiseBuffer = createNoiseBuffer(audioContext);
        const noiseSource = audioContext.createBufferSource();
        const noiseGain = audioContext.createGain();
        const noiseFilter = audioContext.createBiquadFilter();

        noiseSource.buffer = noiseBuffer;
        noiseFilter.type = 'bandpass';
        noiseFilter.frequency.value = 1000;
        noiseFilter.Q.value = 1;

        noiseSource.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(audioContext.destination);

        noiseGain.gain.setValueAtTime(0, t);
        noiseGain.gain.linearRampToValueAtTime(0.4, t + 0.005);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, t + 0.05);

        noiseSource.start(t);
        noiseSource.stop(t + 0.05);

        // 低頻 "Pop"
        const osc = audioContext.createOscillator();
        const oscGain = audioContext.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(150, t);
        osc.frequency.exponentialRampToValueAtTime(40, t + 0.1);

        oscGain.gain.setValueAtTime(0.6, t);
        oscGain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);

        osc.connect(oscGain);
        oscGain.connect(audioContext.destination);

        osc.start(t);
        osc.stop(t + 0.1);
    } catch (error) {
        console.error("Audio error:", error);
    }
};

const createNoiseBuffer = (ctx) => {
    const bufferSize = ctx.sampleRate * 0.1;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const output = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
        output[i] = Math.random() * 2 - 1;
    }
    return buffer;
};

// Play a "clink" sound for finishing a bottle (glass toast)
// Play a "Success Chord" sound (C Major Arpeggio)
const playClinkSound = () => {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;

        const ctx = new AudioContext();
        const t = ctx.currentTime;

        // C Major Chord: C5, E5, G5, C6
        const notes = [523.25, 659.25, 783.99, 1046.50];

        notes.forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, t);

            // Stagger start times slightly for arpeggio effect
            const startTime = t + (i * 0.04);

            gain.gain.setValueAtTime(0, startTime);
            gain.gain.linearRampToValueAtTime(0.2, startTime + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.6);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(startTime);
            osc.stop(startTime + 0.7);
        });
    } catch (e) {
        console.warn("Audio play failed:", e);
    }
};

// Real Fireworks 效果
const triggerFinishAnimation = () => {
    const duration = 2000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 99999 };

    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    const interval = setInterval(function () {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
    }, 250);
};


function WineDetailModal({ visible, wine, onClose, onUpdate }) {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [tempRemaining, setTempRemaining] = useState(100);

    // Sync slider state when wine changes
    useEffect(() => {
        if (wine) {
            setTempRemaining(getSliderValue(wine.remaining_amount));
        }
    }, [wine]);

    if (!wine) return null;

    const handleOpenBottle = async () => {
        try {
            setLoading(true);

            // 1. Play Pop Sound
            playPopSound();

            // 2. Confetti Animation
            const colors = ['#c9a227', '#ffd700', '#ffffff', '#e5e5e5'];

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

            myConfetti({
                particleCount: 150,
                spread: 100,
                origin: { y: 0.5, x: 0.5 },
                colors: colors,
                startVelocity: 45,
                gravity: 1,
                ticks: 300,
            });

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

            setTimeout(() => {
                document.body.removeChild(myCanvas);
            }, 4000);

            // 3. Call API
            const updatedWine = await apiClient.post(`/wine-items/${wine.id}/open`);
            message.success("🍾 開瓶慶祝！請享受您的美酒！");
            onUpdate(updatedWine);

        } catch (error) {
            console.error("Open bottle error:", error);
            message.error("發生錯誤");
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateRemaining = async (value) => {
        // Map slider value
        const map = {
            100: 'full',
            75: '3/4',
            50: '1/2',
            25: '1/4',
            0: 'empty'
        };
        const amount = map[value];
        if (!amount) return;

        // If empty, confirm first!
        if (value === 0) {
            Modal.confirm({
                title: '確定喝完了嗎？',
                content: `「${wine.name}」將標記為已喝完，並從酒窖移除`,
                okText: '確定，已喝完',
                cancelText: '取消',
                okButtonProps: { style: { background: '#c9a227', borderColor: '#c9a227' } },
                onOk: async () => {
                    try {
                        // 1. Play Celebration Effects
                        playClinkSound();
                        triggerFinishAnimation();

                        // 2. Call API
                        await apiClient.post(`/wine-items/${wine.id}/change-status?new_status=consumed`);
                        message.success('🍾 乾杯！已記錄為喝完');

                        // Delay closing slightly
                        setTimeout(() => {
                            onClose();
                            onUpdate({ ...wine, _deleted: true });
                        }, 1500);

                    } catch (error) {
                        console.error("Change status error:", error);
                        message.error('操作失敗，請稍後再試');
                    }
                }
            });
            return;
        }

        try {
            await apiClient.post(`/wine-items/${wine.id}/update-remaining?remaining=${amount}`);
            onUpdate({ ...wine, remaining_amount: amount });
            message.success('已更新剩餘量');
        } catch (error) {
            console.error("Update remaining error:", error);
            message.error('更新失敗');
        }
    };

    const handleChangeStatus = async (newStatus) => {
        const labels = {
            'sold': '已售出',
            'gifted': '已送禮',
            'consumed': '已喝完'
        };

        Modal.confirm({
            title: '確認變更狀態',
            content: `確定要將此酒款標記為「${labels[newStatus]}」嗎？`,
            okText: '確定',
            cancelText: '取消',
            okButtonProps: newStatus === 'consumed' ? { style: { background: '#c9a227', borderColor: '#c9a227' } } : {},
            onOk: async () => {
                try {
                    if (newStatus === 'consumed') {
                        playClinkSound();
                        triggerFinishAnimation();
                    }

                    await apiClient.post(`/wine-items/${wine.id}/change-status?new_status=${newStatus}`);
                    message.success(`已標記為${labels[newStatus]}`);

                    setTimeout(() => {
                        onClose();
                        onUpdate && onUpdate();
                    }, newStatus === 'consumed' ? 2000 : 500);
                } catch (error) {
                    console.error("Change status error:", error);
                    message.error('操作失敗');
                }
            },
        });
    };

    // Helper
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                            <div style={{ flex: 1 }}>
                                <Slider
                                    marks={{
                                        0: '空',
                                        25: '1/4',
                                        50: '半',
                                        75: '3/4',
                                        100: '滿'
                                    }}
                                    step={null}
                                    reverse={true}
                                    value={tempRemaining}
                                    onChange={setTempRemaining}
                                    styles={{
                                        rail: { backgroundColor: '#444' },
                                        track: { backgroundColor: '#c9a227' },
                                        handle: { borderColor: '#c9a227', backgroundColor: '#c9a227' }
                                    }}
                                />
                            </div>
                            <Button
                                type="primary"
                                size="small"
                                onClick={() => handleUpdateRemaining(tempRemaining)}
                                disabled={getSliderValue(wine.remaining_amount) === tempRemaining}
                                style={{
                                    background: '#c9a227',
                                    borderColor: '#c9a227',
                                    color: '#000',
                                    borderRadius: 16,
                                    fontSize: 12,
                                    minWidth: 60
                                }}
                            >
                                儲存
                            </Button>
                        </div>
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

                {/* 拆分按鈕 - 只在 quantity > 1 時顯示 */}
                {wine.quantity > 1 && (
                    <>
                        <Divider style={{ borderColor: '#444', margin: '16px 0' }} />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <Text style={{ color: '#888', whiteSpace: 'nowrap' }}>拆分數量：</Text>
                            <InputNumber
                                min={1}
                                max={wine.quantity - 1}
                                defaultValue={1}
                                style={{ width: 80, background: '#3d3d3d', borderColor: '#555' }}
                                id="split-count-input"
                            />
                            <Button
                                icon={<ScissorOutlined />}
                                onClick={async () => {
                                    const input = document.getElementById('split-count-input');
                                    const splitCount = parseInt(input?.value || 1);
                                    if (splitCount < 1 || splitCount >= wine.quantity) {
                                        message.warning(`拆分數量必須在 1 到 ${wine.quantity - 1} 之間`);
                                        return;
                                    }
                                    try {
                                        const result = await splitWineItem(wine.id, splitCount);
                                        message.success(`已拆分 ${splitCount} 瓶，原酒款剩餘 ${result.original_remaining} 瓶`);
                                        onClose();
                                        onUpdate && onUpdate({ _split: true });
                                    } catch (err) {
                                        message.error('拆分失敗: ' + (err.response?.data?.detail || err.message));
                                    }
                                }}
                                style={{
                                    background: '#3d3d3d',
                                    borderColor: '#555',
                                    color: '#f5f5f5',
                                }}
                            >
                                拆分
                            </Button>
                        </div>
                        <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                            將此酒款拆分成獨立記錄，方便分別追蹤
                        </Text>
                    </>
                )}

                {/* 用途選擇器 */}
                <Divider style={{ borderColor: '#444', margin: '16px 0' }} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Text style={{ color: '#888', whiteSpace: 'nowrap' }}>用途：</Text>
                    <Select
                        value={wine.disposition || 'personal'}
                        style={{ flex: 1 }}
                        onChange={async (value) => {
                            try {
                                await updateWineDisposition(wine.id, value);
                                message.success('已更新用途');
                                onUpdate && onUpdate();
                            } catch (err) {
                                message.error('更新失敗');
                            }
                        }}
                        options={[
                            { value: 'personal', label: '🍷 自飲' },
                            { value: 'gift', label: '🎁 送禮' },
                            { value: 'collection', label: '📦 收藏' },
                        ]}
                    />
                </div>

                {/* 狀態變更按鈕 */}
                <Divider style={{ borderColor: '#444', margin: '24px 0 16px' }} />
                <Text style={{ color: '#888', display: 'block', marginBottom: 12 }}>變更狀態：</Text>
                <Space wrap style={{ width: '100%' }}>
                    <Button
                        size="small"
                        onClick={() => handleChangeStatus('consumed')}
                        style={{ background: '#3d3d3d', color: '#f5f5f5', borderColor: '#555' }}
                    >
                        🍷 標記為喝完
                    </Button>
                    <Button
                        size="small"
                        onClick={() => handleChangeStatus('gifted')}
                        style={{ background: '#3d3d3d', color: '#f5f5f5', borderColor: '#555' }}
                    >
                        🎁 標記為送禮
                    </Button>
                </Space>
            </div>
        </Modal>
    );
}

export default WineDetailModal;
