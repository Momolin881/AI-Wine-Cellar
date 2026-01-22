/**
 * 酒窖設定頁面
 *
 * 管理酒窖資訊、容量設定、新增酒窖
 * Neumorphism 深色主題
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Layout,
    Card,
    Form,
    Input,
    InputNumber,
    Button,
    message,
    Space,
    Typography,
    Spin,
    Modal,
    List,
    Statistic,
    Row,
    Col,
} from 'antd';
import {
    ArrowLeftOutlined,
    PlusOutlined,
    SaveOutlined,
    DeleteOutlined,
    EditOutlined,
} from '@ant-design/icons';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function CellarSettings() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [cellars, setCellars] = useState([]);
    const [selectedCellar, setSelectedCellar] = useState(null);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [addModalVisible, setAddModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [addForm] = Form.useForm();

    useEffect(() => {
        loadCellars();
    }, []);

    const loadCellars = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api/v1/wine-cellars`, {
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const data = await res.json();
            setCellars(data);
        } catch (error) {
            console.error('載入酒窖失敗:', error);
            message.error('載入失敗');
        } finally {
            setLoading(false);
        }
    };

    // 載入酒窖詳情
    const loadCellarDetail = async (cellarId) => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/wine-cellars/${cellarId}`, {
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const data = await res.json();
            return data;
        } catch (error) {
            console.error('載入酒窖詳情失敗:', error);
            return null;
        }
    };

    // 編輯酒窖
    const handleEdit = async (cellar) => {
        const detail = await loadCellarDetail(cellar.id);
        if (detail) {
            setSelectedCellar(detail);
            form.setFieldsValue(detail);
            setEditModalVisible(true);
        }
    };

    // 儲存編輯
    const handleSaveEdit = async (values) => {
        try {
            await fetch(`${API_BASE}/api/v1/wine-cellars/${selectedCellar.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo',
                },
                body: JSON.stringify(values),
            });
            message.success('儲存成功');
            setEditModalVisible(false);
            loadCellars();
        } catch (error) {
            message.error('儲存失敗');
        }
    };

    // 新增酒窖
    const handleAdd = async (values) => {
        try {
            await fetch(`${API_BASE}/api/v1/wine-cellars`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo',
                },
                body: JSON.stringify(values),
            });
            message.success('新增成功');
            setAddModalVisible(false);
            addForm.resetFields();
            loadCellars();
        } catch (error) {
            message.error('新增失敗');
        }
    };

    // 刪除酒窖
    const handleDelete = (cellar) => {
        Modal.confirm({
            title: '確認刪除',
            content: `確定要刪除「${cellar.name}」嗎？所有酒款資料也會一併刪除！`,
            okText: '刪除',
            okType: 'danger',
            cancelText: '取消',
            onOk: async () => {
                try {
                    await fetch(`${API_BASE}/api/v1/wine-cellars/${cellar.id}`, {
                        method: 'DELETE',
                        headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
                    });
                    message.success('已刪除');
                    loadCellars();
                } catch (error) {
                    message.error('刪除失敗');
                }
            },
        });
    };

    if (loading) {
        return (
            <Layout style={{ minHeight: '100vh' }}>
                <Content style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Spin size="large" tip="載入中..." />
                </Content>
            </Layout>
        );
    }

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Content style={{ padding: '16px', maxWidth: 480, margin: '0 auto' }}>
                {/* 標題 */}
                <div style={{ marginBottom: 16 }}>
                    <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
                        返回
                    </Button>
                    <Title level={3} style={{ marginTop: 8 }}>⚙️ 酒窖設定</Title>
                </div>

                {/* 酒窖列表 */}
                <Card className="neu-card" style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                        <Title level={5} style={{ margin: 0 }}>我的酒窖</Title>
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => setAddModalVisible(true)}
                        >
                            新增
                        </Button>
                    </div>

                    {cellars.length === 0 ? (
                        <Text type="secondary">還沒有酒窖，請新增一個</Text>
                    ) : (
                        <List
                            dataSource={cellars}
                            renderItem={(cellar) => (
                                <List.Item
                                    actions={[
                                        <Button
                                            type="text"
                                            icon={<EditOutlined />}
                                            onClick={() => handleEdit(cellar)}
                                        />,
                                        <Button
                                            type="text"
                                            danger
                                            icon={<DeleteOutlined />}
                                            onClick={() => handleDelete(cellar)}
                                        />,
                                    ]}
                                >
                                    <List.Item.Meta
                                        title={cellar.name}
                                        description={cellar.description || `容量：${cellar.total_capacity} 瓶`}
                                    />
                                </List.Item>
                            )}
                        />
                    )}
                </Card>

                {/* 統計（如果有選中酒窖） */}
                {selectedCellar && (
                    <Card className="neu-card">
                        <Title level={5}>{selectedCellar.name} 統計</Title>
                        <Row gutter={16}>
                            <Col span={8}>
                                <Statistic title="酒款數" value={selectedCellar.wine_count} />
                            </Col>
                            <Col span={8}>
                                <Statistic title="已用容量" value={selectedCellar.used_capacity} suffix={`/ ${selectedCellar.total_capacity}`} />
                            </Col>
                            <Col span={8}>
                                <Statistic title="總價值" value={selectedCellar.total_value} prefix="$" />
                            </Col>
                        </Row>
                    </Card>
                )}

                {/* 編輯 Modal */}
                <Modal
                    title="編輯酒窖"
                    open={editModalVisible}
                    onCancel={() => setEditModalVisible(false)}
                    footer={null}
                >
                    <Form form={form} layout="vertical" onFinish={handleSaveEdit}>
                        <Form.Item
                            label="酒窖名稱"
                            name="name"
                            rules={[{ required: true, message: '請輸入名稱' }]}
                        >
                            <Input placeholder="例：家中酒窖" />
                        </Form.Item>

                        <Form.Item label="描述" name="description">
                            <TextArea rows={2} placeholder="描述..." />
                        </Form.Item>

                        <Form.Item
                            label="總容量（瓶位數）"
                            name="total_capacity"
                            rules={[{ required: true, message: '請輸入容量' }]}
                        >
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>

                        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} block>
                            儲存
                        </Button>
                    </Form>
                </Modal>

                {/* 新增 Modal */}
                <Modal
                    title="新增酒窖"
                    open={addModalVisible}
                    onCancel={() => setAddModalVisible(false)}
                    footer={null}
                >
                    <Form
                        form={addForm}
                        layout="vertical"
                        onFinish={handleAdd}
                        initialValues={{ name: '我的酒窖', total_capacity: 100 }}
                    >
                        <Form.Item
                            label="酒窖名稱"
                            name="name"
                            rules={[{ required: true, message: '請輸入名稱' }]}
                        >
                            <Input placeholder="例：家中酒窖" />
                        </Form.Item>

                        <Form.Item label="描述" name="description">
                            <TextArea rows={2} placeholder="描述..." />
                        </Form.Item>

                        <Form.Item
                            label="總容量（瓶位數）"
                            name="total_capacity"
                            rules={[{ required: true, message: '請輸入容量' }]}
                        >
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>

                        <Button type="primary" htmlType="submit" icon={<PlusOutlined />} block>
                            新增酒窖
                        </Button>
                    </Form>
                </Modal>
            </Content>
        </Layout>
    );
}

export default CellarSettings;
