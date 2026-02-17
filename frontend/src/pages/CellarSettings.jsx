/**
 * 酒窖設定頁面
 *
 * 管理酒窖資訊、容量設定
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Layout,
    Card,
    Form,
    Input,
    Button,
    message,
    Typography,
    Spin,
    Modal,
    Segmented,
} from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useMode } from '../contexts/ModeContext';
import apiClient, { getFoodItems } from '../services/api';
import '../styles/OnboardingQuest.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

function CellarSettings() {
    const navigate = useNavigate();
    const { mode, setMode, theme } = useMode();
    const [loading, setLoading] = useState(true);
    const [cellars, setCellars] = useState([]);
    const [selectedCellar, setSelectedCellar] = useState(null);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [questDone, setQuestDone] = useState(false);

    useEffect(() => {
        loadCellars();
    }, []);

    // 檢查新手三部曲是否完成
    useEffect(() => {
        const checkQuest = async () => {
            try {
                const items = await getFoodItems({ status: 'active' });
                const hasScan = Array.isArray(items) && items.some(i => i.recognized_by_ai === 1);
                const hasOpen = Array.isArray(items) && items.some(i => i.bottle_status === 'opened');

                let hasInvite = false;
                try {
                    const invitations = await apiClient.get('/invitations');
                    hasInvite = Array.isArray(invitations) && invitations.length > 0;
                } catch { /* ignore */ }

                setQuestDone(hasScan && hasInvite && hasOpen);
            } catch {
                setQuestDone(false);
            }
        };
        checkQuest();
    }, []);

    // 模式切換（含新手鎖定）
    const handleModeChange = (selectedMode) => {
        if (selectedMode === 'pro' && !questDone) {
            Modal.info({
                title: '🏆 先完成新手三部曲！',
                content: (
                    <div style={{ color: '#ccc', lineHeight: 1.8 }}>
                        <p>完成以下任務即可解鎖 <strong style={{ color: '#00f0ff' }}>Pro Mode</strong>：</p>
                        <p>📸 拍照入庫一支酒</p>
                        <p>🥂 揪喝分享一位酒友</p>
                        <p>🍷 完成一次開瓶儀式</p>
                        <p style={{ marginTop: 12, fontSize: 13, color: '#888' }}>
                            先用 Chill Mode 體驗吧！
                        </p>
                    </div>
                ),
                okText: '了解',
                styles: {
                    content: { background: '#252538', borderRadius: 12 },
                    header: { background: '#252538', color: '#fff', borderBottom: '1px solid #2a2a4a' },
                    body: { background: '#252538' },
                    footer: { background: '#252538', borderTop: '1px solid #2a2a4a' },
                    mask: { background: 'rgba(0,0,0,0.7)' },
                },
                className: 'onboarding-quest-modal',
            });
            return;
        }
        setMode(selectedMode);
    };

    const loadCellars = async (showLoading = true) => {
        try {
            if (showLoading) setLoading(true);
            const data = await apiClient.get('/wine-cellars');
            const cellarList = Array.isArray(data) ? data : [];
            setCellars(cellarList);
            return cellarList;
        } catch (error) {
            console.error('載入酒窖失敗:', error);
            message.error('載入失敗');
            setCellars([]);
            return [];
        } finally {
            if (showLoading) setLoading(false);
        }
    };

    const loadCellarDetail = async (cellarId) => {
        try {
            const data = await apiClient.get(`/wine-cellars/${cellarId}`);
            return data;
        } catch (error) {
            console.error('載入酒窖詳情失敗:', error);
            return null;
        }
    };

    const handleEdit = async (cellar) => {
        try {
            let cellarId = cellar?.id;
            if (!cellarId) {
                const data = await apiClient.get('/wine-cellars');
                if (Array.isArray(data) && data.length > 0) {
                    cellarId = data[0].id;
                    setCellars(data);
                } else {
                    message.error('找不到酒窖');
                    return;
                }
            }
            const detail = await loadCellarDetail(cellarId);
            if (detail) {
                setSelectedCellar(detail);
                form.setFieldsValue(detail);
                setEditModalVisible(true);
            }
        } catch (error) {
            console.error('開啟編輯失敗:', error);
            message.error('開啟編輯失敗');
        }
    };

    const handleSaveEdit = async (values) => {
        const cellarId = selectedCellar?.id || cellars[0]?.id;
        if (!cellarId) {
            message.error('找不到酒窖');
            return;
        }
        try {
            if (!values.total_capacity) {
                values.total_capacity = 50;
            }
            await apiClient.put(`/wine-cellars/${cellarId}`, values);
            message.success('儲存成功');
            setEditModalVisible(false);
            loadCellars();
        } catch (error) {
            console.error('儲存失敗:', error);
            message.error('儲存失敗');
        }
    };

    if (loading) {
        return (
            <Layout style={{ minHeight: '100vh', background: theme.background }}>
                <Content style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Spin size="large" />
                </Content>
            </Layout>
        );
    }

    return (
        <Layout style={{ minHeight: '100vh', background: theme.background }}>
            <Content style={{ padding: '16px', maxWidth: 480, margin: '0 auto' }}>
                {/* 標題 */}
                <div style={{ marginBottom: 16 }}>
                    <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
                        返回
                    </Button>
                    <Title level={3} style={{ marginTop: 8 }}>⚙️ 酒窖設定</Title>
                </div>

                {/* Mode 切換 */}
                <Card style={{ marginBottom: 16, background: theme.card, border: 'none' }}>
                    <div style={{ marginBottom: 12 }}>
                        <Title level={5} style={{ margin: 0 }}>🎨 模式設定</Title>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            快速入庫馬上揪喝
                        </Text>
                    </div>
                    <Segmented
                        value={mode}
                        onChange={handleModeChange}
                        block
                        options={[
                            {
                                label: (
                                    <div style={{ padding: '8px 0' }}>
                                        <div style={{ fontSize: 24 }}>🎮</div>
                                        <div style={{ fontSize: 13, fontWeight: 600, color: mode === 'chill' ? '#fff' : '#aaa' }}>Chill</div>
                                        <div style={{ fontSize: 10, color: mode === 'chill' ? '#ddd' : '#888' }}>玩家模式</div>
                                    </div>
                                ),
                                value: 'chill',
                            },
                            {
                                label: (
                                    <div style={{ padding: '8px 0' }}>
                                        <div style={{ fontSize: 24 }}>{questDone ? '🏆' : '🔒'}</div>
                                        <div style={{ fontSize: 13, fontWeight: 600, color: mode === 'pro' ? '#fff' : '#aaa' }}>Pro</div>
                                        <div style={{ fontSize: 10, color: mode === 'pro' ? '#ddd' : '#888' }}>{questDone ? '達人模式' : '完成三部曲解鎖'}</div>
                                    </div>
                                ),
                                value: 'pro',
                            },
                        ]}
                    />
                </Card>

                {/* 我的酒窖 */}
                <Card style={{ marginBottom: 16, background: theme.card, border: 'none' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Title level={5} style={{ margin: 0 }}>我的酒窖</Title>
                        <Button
                            type="primary"
                            size="small"
                            onClick={() => handleEdit(cellars[0])}
                        >
                            + 編輯
                        </Button>
                    </div>
                    <div
                        onClick={() => handleEdit(cellars[0])}
                        style={{ cursor: 'pointer', marginTop: 12 }}
                    >
                        <Text type="secondary">查看我的專屬設定</Text>
                    </div>
                </Card>

                {/* 統計（如果有選中酒窖） */}
                {selectedCellar && (
                    <Card style={{ background: theme.card, border: 'none' }}>
                        <Title level={5}>{selectedCellar.name} 統計</Title>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                            <div style={{ textAlign: 'center', flex: 1 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>總酒數</Text>
                                <Text strong style={{ fontSize: 20, color: theme.primary }}>{selectedCellar.wine_count}</Text>
                                <Text type="secondary" style={{ fontSize: 12 }}> 瓶</Text>
                            </div>
                            <div style={{ textAlign: 'center', flex: 1 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>已用容量</Text>
                                <Text strong style={{ fontSize: 20, color: theme.primary }}>{selectedCellar.used_capacity}</Text>
                                <Text type="secondary" style={{ fontSize: 12 }}> / {selectedCellar.total_capacity} 瓶</Text>
                            </div>
                            <div style={{ textAlign: 'center', flex: 1 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>總價值</Text>
                                <Text strong style={{ fontSize: 20, color: theme.primary }}>$ {selectedCellar.total_value?.toLocaleString()}</Text>
                            </div>
                        </div>
                    </Card>
                )}

                {/* 編輯 Modal */}
                <Modal
                    title="我的酒窖"
                    open={editModalVisible}
                    onCancel={() => setEditModalVisible(false)}
                    footer={null}
                    styles={{
                        content: { background: theme.background, border: `1px solid ${theme.border}` },
                        header: { background: theme.background, borderBottom: `1px solid ${theme.border}` },
                        body: { background: theme.background },
                    }}
                >
                    <Form form={form} layout="vertical" onFinish={handleSaveEdit}>
                        <Form.Item
                            label="酒窖名稱"
                            name="name"
                            rules={[{ required: true, message: '請輸入名稱' }]}
                        >
                            <Input placeholder="例：momo land" />
                        </Form.Item>

                        <Form.Item label="描述" name="description">
                            <TextArea rows={2} placeholder="描述..." />
                        </Form.Item>

                        <Form.Item
                            label="總容量（瓶位數）"
                            name="total_capacity"
                        >
                            <Input type="number" min={1} placeholder="50" />
                        </Form.Item>

                        <Button type="primary" htmlType="submit" block>
                            + 儲存
                        </Button>
                    </Form>
                </Modal>
            </Content>
        </Layout>
    );
}

export default CellarSettings;
