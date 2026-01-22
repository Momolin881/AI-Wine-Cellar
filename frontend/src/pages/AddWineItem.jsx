/**
 * 新增酒款頁面
 *
 * 支援 AI 酒標辨識和手動輸入
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
    Select,
    Button,
    DatePicker,
    message,
    Space,
    Typography,
    Upload,
    Spin,
} from 'antd';
import {
    ArrowLeftOutlined,
    CameraOutlined,
    SaveOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const wineTypes = ['紅酒', '白酒', '粉紅酒', '氣泡酒', '香檳', '威士忌', '白蘭地', '伏特加', '清酒', '啤酒', '其他'];
const containerTypes = ['瓶', '箱', '桶'];

function AddWineItem() {
    const navigate = useNavigate();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [recognizing, setRecognizing] = useState(false);
    const [imageUrl, setImageUrl] = useState(null);
    const [cloudinaryPublicId, setCloudinaryPublicId] = useState(null);
    const [cellars, setCellars] = useState([]);
    const [selectedCellar, setSelectedCellar] = useState(null);

    useEffect(() => {
        loadCellars();
    }, []);

    const loadCellars = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/wine-cellars`, {
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
            });
            const data = await res.json();
            setCellars(data);
            if (data.length > 0) {
                setSelectedCellar(data[0].id);
                form.setFieldsValue({ cellar_id: data[0].id });
            }
        } catch (error) {
            console.error('載入酒窖失敗:', error);
        }
    };

    // AI 酒標辨識
    const handleImageUpload = async (file) => {
        if (!selectedCellar) {
            message.warning('請先選擇酒窖');
            return false;
        }

        try {
            setRecognizing(true);

            const formData = new FormData();
            formData.append('image', file);
            formData.append('cellar_id', selectedCellar);

            const res = await fetch(`${API_BASE}/api/v1/wine-items/recognize`, {
                method: 'POST',
                headers: { 'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo' },
                body: formData,
            });

            if (!res.ok) throw new Error('辨識失敗');

            const data = await res.json();

            // 填入表單
            form.setFieldsValue({
                name: data.name,
                wine_type: data.wine_type,
                brand: data.brand,
                vintage: data.vintage,
                region: data.region,
                country: data.country,
                abv: data.abv,
                storage_temp: data.suggested_storage_temp,
                notes: data.description,
            });

            setImageUrl(data.image_url);
            setCloudinaryPublicId(data.cloudinary_public_id);

            message.success('辨識成功！');
        } catch (error) {
            console.error('AI 辨識失敗:', error);
            message.error('辨識失敗，請手動輸入');
        } finally {
            setRecognizing(false);
        }

        return false; // 阻止 Upload 預設行為
    };

    // 提交表單
    const handleSubmit = async (values) => {
        if (!selectedCellar) {
            message.warning('請先選擇酒窖');
            return;
        }

        try {
            setLoading(true);

            const payload = {
                ...values,
                cellar_id: selectedCellar,
                image_url: imageUrl,
                cloudinary_public_id: cloudinaryPublicId,
                purchase_date: values.purchase_date?.format('YYYY-MM-DD'),
                optimal_drinking_start: values.optimal_drinking_start?.format('YYYY-MM-DD'),
                optimal_drinking_end: values.optimal_drinking_end?.format('YYYY-MM-DD'),
                recognized_by_ai: recognizing ? 1 : 0,
            };

            const res = await fetch(`${API_BASE}/api/v1/wine-items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Line-User-Id': localStorage.getItem('lineUserId') || 'demo',
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error('新增失敗');

            message.success('新增成功！');
            navigate('/');
        } catch (error) {
            console.error('新增酒款失敗:', error);
            message.error('新增失敗，請稍後再試');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Content style={{ padding: '16px', maxWidth: 480, margin: '0 auto' }}>
                {/* 標題 */}
                <div style={{ marginBottom: 16 }}>
                    <Button
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate('/')}
                        style={{ marginBottom: 8 }}
                    >
                        返回
                    </Button>
                    <Title level={3}>🍷 新增酒款</Title>
                </div>

                {/* AI 辨識區塊 */}
                <Card className="neu-card" style={{ marginBottom: 16, textAlign: 'center' }}>
                    <Upload
                        accept="image/*"
                        showUploadList={false}
                        beforeUpload={handleImageUpload}
                        capture="environment"
                    >
                        {recognizing ? (
                            <div style={{ padding: 40 }}>
                                <Spin size="large" tip="AI 辨識中..." />
                            </div>
                        ) : imageUrl ? (
                            <img
                                src={imageUrl}
                                alt="酒標"
                                style={{
                                    width: '100%',
                                    maxHeight: 200,
                                    objectFit: 'contain',
                                    borderRadius: 12,
                                    marginBottom: 8,
                                }}
                            />
                        ) : (
                            <div style={{ padding: 40 }}>
                                <CameraOutlined style={{ fontSize: 48, color: 'var(--accent-gold)' }} />
                                <div style={{ marginTop: 8 }}>
                                    <Text type="secondary">拍攝酒標，AI 自動辨識</Text>
                                </div>
                            </div>
                        )}
                    </Upload>
                </Card>

                {/* 表單 */}
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{
                        wine_type: '紅酒',
                        quantity: 1,
                        space_units: 1,
                        container_type: '瓶',
                        bottle_status: 'unopened',
                        remaining_amount: 'full',
                        purchase_date: dayjs(),
                    }}
                >
                    {/* 酒窖選擇 */}
                    <Form.Item label="酒窖" name="cellar_id">
                        <Select
                            value={selectedCellar}
                            onChange={setSelectedCellar}
                            placeholder="選擇酒窖"
                        >
                            {cellars.map((cellar) => (
                                <Option key={cellar.id} value={cellar.id}>
                                    {cellar.name}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>

                    {/* 基本資訊 */}
                    <Form.Item
                        label="酒名"
                        name="name"
                        rules={[{ required: true, message: '請輸入酒名' }]}
                    >
                        <Input placeholder="例：Château Margaux 2018" />
                    </Form.Item>

                    <Form.Item
                        label="酒類"
                        name="wine_type"
                        rules={[{ required: true, message: '請選擇酒類' }]}
                    >
                        <Select placeholder="選擇酒類">
                            {wineTypes.map((type) => (
                                <Option key={type} value={type}>{type}</Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="品牌/酒莊" name="brand" style={{ flex: 1 }}>
                            <Input placeholder="例：波爾多" />
                        </Form.Item>
                        <Form.Item label="年份" name="vintage" style={{ width: 100 }}>
                            <InputNumber
                                min={1900}
                                max={new Date().getFullYear()}
                                placeholder="2018"
                                style={{ width: '100%' }}
                            />
                        </Form.Item>
                    </Space>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="產區" name="region" style={{ flex: 1 }}>
                            <Input placeholder="例：波爾多" />
                        </Form.Item>
                        <Form.Item label="國家" name="country" style={{ flex: 1 }}>
                            <Input placeholder="例：法國" />
                        </Form.Item>
                    </Space>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="酒精濃度 (%)" name="abv" style={{ flex: 1 }}>
                            <InputNumber
                                min={0}
                                max={100}
                                step={0.1}
                                placeholder="13.5"
                                style={{ width: '100%' }}
                            />
                        </Form.Item>
                        <Form.Item label="數量" name="quantity" style={{ flex: 1 }}>
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>
                    </Space>

                    {/* 價格 */}
                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label="進貨價 (NT$)" name="purchase_price" style={{ flex: 1 }}>
                            <InputNumber
                                min={0}
                                placeholder="1500"
                                style={{ width: '100%' }}
                            />
                        </Form.Item>
                        <Form.Item label="零售價 (NT$)" name="retail_price" style={{ flex: 1 }}>
                            <InputNumber
                                min={0}
                                placeholder="2000"
                                style={{ width: '100%' }}
                            />
                        </Form.Item>
                    </Space>

                    {/* 日期 */}
                    <Form.Item label="購買日期" name="purchase_date">
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>

                    {/* 儲存位置 */}
                    <Form.Item label="存放位置" name="storage_location">
                        <Input placeholder="例：A架第2層" />
                    </Form.Item>

                    {/* 備註 */}
                    <Form.Item label="備註" name="notes">
                        <TextArea rows={3} placeholder="品酒筆記、特殊說明..." />
                    </Form.Item>

                    {/* 提交按鈕 */}
                    <Form.Item>
                        <Button
                            type="primary"
                            htmlType="submit"
                            icon={<SaveOutlined />}
                            loading={loading}
                            size="large"
                            block
                        >
                            儲存酒款
                        </Button>
                    </Form.Item>
                </Form>
            </Content>
        </Layout>
    );
}

export default AddWineItem;
