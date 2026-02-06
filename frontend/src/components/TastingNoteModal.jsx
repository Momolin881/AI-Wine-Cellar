/**
 * 品飲筆記 Modal
 *
 * 喝完酒時跳出，讓用戶記錄評分、風味標籤、香氣、口感、餘韻
 */

import { useState } from 'react';
import { Modal, Rate, Input, Tag, Typography, message, Slider, Collapse, Row, Col } from 'antd';
import { CaretRightOutlined } from '@ant-design/icons';
import apiClient from '../services/api';
import FlavorRadar from './FlavorRadar';

// 翻書音效
const playPageFlipSound = () => {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;

        const ctx = new AudioContext();
        const t = ctx.currentTime;

        // 模擬紙張翻動的沙沙聲 - 使用白噪音 + 濾波
        const bufferSize = ctx.sampleRate * 0.15;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 2);
        }

        const noise = ctx.createBufferSource();
        noise.buffer = buffer;

        const filter = ctx.createBiquadFilter();
        filter.type = 'highpass';
        filter.frequency.value = 2000;

        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.3, t);
        gain.gain.exponentialRampToValueAtTime(0.01, t + 0.15);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);

        noise.start(t);
        noise.stop(t + 0.15);

        // 第二層：輕柔的 "叮" 聲
        const osc = ctx.createOscillator();
        const oscGain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1200, t + 0.1);
        osc.frequency.exponentialRampToValueAtTime(800, t + 0.3);

        oscGain.gain.setValueAtTime(0, t + 0.1);
        oscGain.gain.linearRampToValueAtTime(0.15, t + 0.12);
        oscGain.gain.exponentialRampToValueAtTime(0.001, t + 0.4);

        osc.connect(oscGain);
        oscGain.connect(ctx.destination);

        osc.start(t + 0.1);
        osc.stop(t + 0.4);
    } catch (e) {
        console.warn('Audio play failed:', e);
    }
};

const { TextArea } = Input;
const { Text, Title } = Typography;

// 風味標籤選項
const FLAVOR_OPTIONS = [
    { label: '果香', value: 'fruity', color: '#ff6b6b' },
    { label: '花香', value: 'floral', color: '#f06595' },
    { label: '木質', value: 'woody', color: '#a0522d' },
    { label: '香料', value: 'spicy', color: '#ff922b' },
    { label: '草本', value: 'herbal', color: '#51cf66' },
    { label: '礦物', value: 'mineral', color: '#868e96' },
    { label: '煙燻', value: 'smoky', color: '#495057' },
    { label: '奶油', value: 'buttery', color: '#ffd43b' },
    { label: '蜂蜜', value: 'honey', color: '#fab005' },
    { label: '堅果', value: 'nutty', color: '#d9480f' },
    { label: '巧克力', value: 'chocolate', color: '#5c3d2e' },
    { label: '咖啡', value: 'coffee', color: '#6f4e37' },
];

function TastingNoteModal({ visible, wine, onClose, onSave }) {
    const [rating, setRating] = useState(3);
    const [review, setReview] = useState('');
    const [selectedTags, setSelectedTags] = useState([]);
    const [aroma, setAroma] = useState('');
    const [palate, setPalate] = useState('');
    const [finish, setFinish] = useState('');
    // 風味雷達數據
    const [flavorData, setFlavorData] = useState({
        acidity: 3,
        tannin: 3,
        body: 3,
        sweetness: 3,
        alcohol_feel: 3
    });
    const [saving, setSaving] = useState(false);

    const handleTagClick = (value) => {
        if (selectedTags.includes(value)) {
            setSelectedTags(selectedTags.filter(t => t !== value));
        } else {
            setSelectedTags([...selectedTags, value]);
        }
    };

    const handleSave = async () => {
        if (!wine?.id) return;

        try {
            setSaving(true);
            // sync_tasting_notes=true 會同步到同批次的其他瓶
            await apiClient.put(`/wine-items/${wine.id}?sync_tasting_notes=true`, {
                rating,
                review,
                flavor_tags: JSON.stringify(selectedTags),
                aroma,
                palate,
                aroma,
                palate,
                finish,
                ...flavorData,
            });

            // 播放翻書音效
            playPageFlipSound();

            // 顯示完成訊息
            message.success('Drink, Relax, Enjoy! 已收錄💫');
            onSave?.();
            onClose();
        } catch (error) {
            console.error('儲存品飲筆記失敗:', error);
            message.error('儲存失敗');
        } finally {
            setSaving(false);
        }
    };

    const handleSkip = () => {
        onSave?.();
        onClose();
    };

    return (
        <Modal
            title={
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 32, marginBottom: 8 }}>📝</div>
                    <Title level={4} style={{ margin: 0, color: '#333' }}>
                        留下品飲筆記和時光✨
                    </Title>
                    <Text type="secondary">{wine?.name}</Text>
                </div>
            }
            open={visible}
            onCancel={handleSkip}
            okText="儲存"
            cancelText="跳過"
            onOk={handleSave}
            confirmLoading={saving}
            width={400}
            centered
            styles={{
                content: { background: '#f5f5f5', borderRadius: 16 },
                header: { background: '#f5f5f5', borderBottom: 'none', paddingBottom: 0 },
                body: { background: '#f5f5f5', paddingTop: 16 },
                footer: { background: '#f5f5f5', borderTop: 'none' },
            }}
        >
            {/* 評分 */}
            <div style={{ marginBottom: 24 }}>
                <Text strong style={{ display: 'block', marginBottom: 12, color: '#333' }}>
                    ⭐ 評分
                </Text>
                <Rate
                    allowHalf
                    value={rating}
                    onChange={setRating}
                    style={{ color: '#c9a227', fontSize: 32 }}
                />
            </div>

            {/* 評價 */}
            <div style={{ marginBottom: 24 }}>
                <Text strong style={{ display: 'block', marginBottom: 8, color: '#333' }}>
                    💬 評價
                </Text>
                <TextArea
                    value={review}
                    onChange={(e) => setReview(e.target.value)}
                    placeholder="對這支酒的整體評價..."
                    autoSize={{ minRows: 2, maxRows: 3 }}
                    style={{ borderRadius: 8 }}
                />
            </div>

            {/* 風味標籤 */}
            <div style={{ marginBottom: 24 }}>
                <Text strong style={{ display: 'block', marginBottom: 12, color: '#333' }}>
                    風味標籤
                </Text>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {FLAVOR_OPTIONS.map(option => (
                        <Tag
                            key={option.value}
                            color={selectedTags.includes(option.value) ? option.color : 'default'}
                            onClick={() => handleTagClick(option.value)}
                            style={{
                                cursor: 'pointer',
                                borderRadius: 16,
                                padding: '4px 12px',
                                border: selectedTags.includes(option.value) ? 'none' : '1px solid #d9d9d9',
                            }}
                        >
                            {option.label}
                        </Tag>
                    ))}
                </div>
            </div>

            {/* 香氣 */}
            <div style={{ marginBottom: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 8, color: '#333' }}>
                    🌸 香氣
                </Text>
                <TextArea
                    value={aroma}
                    onChange={(e) => setAroma(e.target.value)}
                    placeholder="描述聞到的香氣..."
                    autoSize={{ minRows: 2, maxRows: 3 }}
                    style={{ borderRadius: 8 }}
                />
            </div>

            {/* 口感 */}
            <div style={{ marginBottom: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 8, color: '#333' }}>
                    👅 口感
                </Text>
                <TextArea
                    value={palate}
                    onChange={(e) => setPalate(e.target.value)}
                    placeholder="描述入口的感受..."
                    autoSize={{ minRows: 2, maxRows: 3 }}
                    style={{ borderRadius: 8 }}
                />
            </div>

            {/* 餘韻 */}
            <div style={{ marginBottom: 8 }}>
                <Text strong style={{ display: 'block', marginBottom: 8, color: '#333' }}>
                    ✨ 餘韻
                </Text>
                <TextArea
                    value={finish}
                    onChange={(e) => setFinish(e.target.value)}
                    placeholder="描述吞嚥後的尾韻..."
                    autoSize={{ minRows: 2, maxRows: 3 }}
                    style={{ borderRadius: 8 }}
                />
            </div>
        </div>

            {/* 進階風味分析 (Pro) - 折疊區塊 */ }
    <Collapse
        ghost
        expandIcon={({ isActive }) => <CaretRightOutlined rotate={isActive ? 90 : 0} />}
        items={[
            {
                key: '1',
                label: <span style={{ fontWeight: 'bold', color: '#333' }}>📊 進階風味分析 (Pro)</span>,
                children: (
                    <div>
                        <Row gutter={24}>
                            {/* 左側：雷達圖 */}
                            <Col span={24} md={10} style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                                <FlavorRadar data={flavorData} />
                            </Col>

                            {/* 右側：滑桿 */}
                            <Col span={24} md={14}>
                                {[
                                    { key: 'acidity', label: '酸度' },
                                    { key: 'tannin', label: '單寧' },
                                    { key: 'body', label: '酒體' },
                                    { key: 'sweetness', label: '甜度' },
                                    { key: 'alcohol_feel', label: '酒感' },
                                ].map(item => (
                                    <div key={item.key} style={{ marginBottom: 8 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Text style={{ fontSize: 12, color: '#666' }}>{item.label}</Text>
                                            <Text style={{ fontSize: 12, color: '#c9a227' }}>{flavorData[item.key]}</Text>
                                        </div>
                                        <Slider
                                            min={1}
                                            max={5}
                                            value={flavorData[item.key]}
                                            onChange={(val) => setFlavorData(prev => ({ ...prev, [item.key]: val }))}
                                            styles={{
                                                rail: { backgroundColor: '#ddd' },
                                                track: { backgroundColor: '#c9a227' },
                                                handle: { borderColor: '#c9a227', backgroundColor: '#c9a227' }
                                            }}
                                        />
                                    </div>
                                ))}
                            </Col>
                        </Row>
                    </div>
                ),
            }
        ]}
    />
        </Modal >
    );
}

export default TastingNoteModal;
