/**
 * 編輯酒款頁面
 *
 * 顯示酒款詳情，支援編輯、開瓶、更新剩餘量、變更狀態
 * Neumorphism 深色主題
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    Layout,
    Card,
    Form,
    Input,
    InputNumber,
    Select,
    Button,
    Radio,
    DatePicker,
    message,
    Space,
    Typography,
    Spin,
    Divider,
    Modal,
} from 'antd';
import {
    ArrowLeftOutlined,
    SaveOutlined,
    DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const wineTypes = ['紅酒', '白酒', '粉紅酒', '氣泡酒', '香檳', '威士忌', '白蘭地', '伏特加', '清酒', '啤酒', '其他'];
const remainingOptions = ['full', '3/4', '1/2', '1/4', 'empty'];
const remainingLabels = {
    'full': '滿瓶',
    '3/4': '3/4',
    '1/2': '1/2',
    '1/4': '1/4',
    'empty': '空瓶',
};

function EditWineItem() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [item, setItem] = useState(null);

    useEffect(() => {
        loadItem();
    }, [id]);

    const loadItem = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api/v1/wine-items/${id}`, {
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const data = await res.json();
            setItem(data);

            // 填入表單
            form.setFieldsValue({
                ...data,
                purchase_date: data.purchase_date ? dayjs(data.purchase_date) : null,
                optimal_drinking_start: data.optimal_drinking_start ? dayjs(data.optimal_drinking_start) : null,
                optimal_drinking_end: data.optimal_drinking_end ? dayjs(data.optimal_drinking_end) : null,
            });
        } catch (error) {
            console.error('載入酒款失敗:', error);
            message.error('載入失敗');
        } finally {
            setLoading(false);
        }
    };

    // 開瓶
    const handleOpenBottle = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/wine-items/${id}/open`, {
                method: 'POST',
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const data = await res.json();
            setItem(data);
            form.setFieldsValue(data);
            message.success('已標記為開瓶！');
        } catch (error) {
            message.error('操作失敗');
        }
    };

    // 更新剩餘量
    const handleUpdateRemaining = async (remaining) => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/wine-items/${id}/update-remaining?remaining=${remaining}`, {
                method: 'POST',
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const data = await res.json();
            setItem(data);
            form.setFieldsValue(data);
            message.success('已更新剩餘量');
        } catch (error) {
            message.error('操作失敗');
        }
    };

    // 變更狀態
    const handleChangeStatus = async (newStatus) => {
        Modal.confirm({
            title: '確認變更狀態',
            content: `確定要將此酒款標記為「${statusLabels[newStatus]}」嗎？`,
            okText: '確定',
            cancelText: '取消',
            onOk: async () => {
                try {
                    const res = await fetch(`${API_BASE}/api/v1/wine-items/${id}/change-status?new_status=${newStatus}`, {
                        method: 'POST',
                        headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
                    });
                    const data = await res.json();
                    setItem(data);
                    message.success('狀態已變更');
                    navigate('/');
                } catch (error) {
                    message.error('操作失敗');
                }
            },
        });
    };

    // 儲存編輯
    const handleSubmit = async (values) => {
        try {
            setSaving(true);

            const payload = {
                ...values,
                purchase_date: values.purchase_date?.format('YYYY-MM-DD'),
                optimal_drinking_start: values.optimal_drinking_start?.format('YYYY-MM-DD'),
                optimal_drinking_end: values.optimal_drinking_end?.format('YYYY-MM-DD'),
            };

            await fetch(`${API_BASE}/api/v1/wine-items/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo',
                },
                body: JSON.stringify(payload),
            });

            message.success('儲存成功！');
            navigate('/');
        } catch (error) {
            message.error('儲存失敗');
        } finally {
            setSaving(false);
        }
    };

    // 刪除
    const handleDelete = async () => {
        Modal.confirm({
            title: '確認刪除',
            content: '確定要刪除這支酒嗎？此操作無法復原。',
            okText: '刪除',
            okType: 'danger',
            cancelText: '取消',
            onOk: async () => {
                await fetch(`${API_BASE}/api/v1/wine-items/${id}`, {
                    method: 'DELETE',
                    headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
                });
                message.success('已刪除');
                navigate('/');
            },
        });
    };

    const statusLabels = {
        'active': '在庫',
        'sold': '已售出',
        'gifted': '已送禮',
        'consumed': '已喝完',
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
                    <Title level={3} style={{ marginTop: 8 }}>編輯酒款</Title>
                </div>

                {/* 圖片 */}
                {item?.image_url && (
                    <Card className="neu-card" style={{ marginBottom: 16, textAlign: 'center' }}>
                        <img
                            src={item.image_url}
                            alt={item.name}
                            style={{ maxWidth: '100%', maxHeight: 200, objectFit: 'contain', borderRadius: 12 }}
                        />
                    </Card>
                )}

                {/* 開瓶狀態操作 */}
                {item?.status === 'active' && (
                    <Card className="neu-card" style={{ marginBottom: 16 }}>
                        <Title level={5}>🍷 開瓶狀態</Title>

                        {item.bottle_status === 'unopened' ? (
                            <Button type="primary" onClick={handleOpenBottle} block>
                                開瓶
                            </Button>
                        ) : (
                            <div>
                                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                                    剩餘量：{remainingLabels[item.remaining_amount]}
                                </Text>
                                <Space wrap>
                                    {remainingOptions.map((opt) => (
                                        <Button
                                            key={opt}
                                            type={item.remaining_amount === opt ? 'primary' : 'default'}
                                            onClick={() => handleUpdateRemaining(opt)}
                                        >
                                            {remainingLabels[opt]}
                                        </Button>
                                    ))}
                                </Space>
                            </div>
                        )}
                    </Card>
                )}

                {/* 狀態變更 */}
                {item?.status === 'active' && (
                    <Card className="neu-card" style={{ marginBottom: 16 }}>
                        <Title level={5}>📤 變更狀態</Title>
                        <Space wrap>
                            <Button onClick={() => handleChangeStatus('sold')}>標記為售出</Button>
                            <Button onClick={() => handleChangeStatus('gifted')}>標記為送禮</Button>
                            <Button onClick={() => handleChangeStatus('consumed')}>標記為喝完</Button>
                        </Space>
                    </Card>
                )}

                {/* 表單 */}
                <Form form={form} layout="vertical" onFinish={handleSubmit}>
                    <Form.Item label="酒名" name="name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>

                    <Form.Item label="酒類" name="wine_type" rules={[{ required: true }]}>
                        <Select>
                            {wineTypes.map((t) => <Option key={t} value={t}>{t}</Option>)}
                        </Select>
                    </Form.Item>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="品牌/酒莊" name="brand" style={{ flex: 1 }}>
                            <Input />
                        </Form.Item>
                        <Form.Item label="年份" name="vintage" style={{ width: 100 }}>
                            <InputNumber style={{ width: '100%' }} />
                        </Form.Item>
                    </Space>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="產區" name="region" style={{ flex: 1 }}>
                            <Input />
                        </Form.Item>
                        <Form.Item label="國家" name="country" style={{ flex: 1 }}>
                            <Input />
                        </Form.Item>
                    </Space>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="酒精濃度 (%)" name="abv" style={{ flex: 1 }}>
                            <InputNumber step={0.1} style={{ width: '100%' }} />
                        </Form.Item>
                        <Form.Item label="數量" name="quantity" style={{ flex: 1 }}>
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>
                    </Space>



                    <Form.Item label="保存類型 (影響開瓶後建議飲用期)" name="preservation_type" rules={[{ required: true }]}>
                        <Radio.Group buttonStyle="solid">
                            <Radio.Button value="immediate">即飲型 (3-5天)</Radio.Button>
                            <Radio.Button value="aging">陳年型 (較長)</Radio.Button>
                        </Radio.Group>
                    </Form.Item>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="進貨價 (NT$)" name="purchase_price" style={{ flex: 1 }}>
                            <InputNumber min={0} style={{ width: '100%' }} />
                        </Form.Item>
                        <Form.Item label="零售價 (NT$)" name="retail_price" style={{ flex: 1 }}>
                            <InputNumber min={0} style={{ width: '100%' }} />
                        </Form.Item>
                    </Space>

                    <Form.Item label="存放位置" name="storage_location">
                        <Input />
                    </Form.Item>

                    <Form.Item label="備註" name="notes">
                        <TextArea rows={3} />
                    </Form.Item>

                    <Form.Item label="品酒筆記" name="tasting_notes">
                        <TextArea rows={3} placeholder="香氣、口感、餘韻..." />
                    </Form.Item>

                    <Divider />

                    <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving} block>
                        儲存變更
                    </Button>

                    <Button danger icon={<DeleteOutlined />} onClick={handleDelete} block style={{ marginTop: 8 }}>
                        刪除此酒款
                    </Button>
                </Form>
            </Content>
        </Layout >
    );
}

export default EditWineItem;
