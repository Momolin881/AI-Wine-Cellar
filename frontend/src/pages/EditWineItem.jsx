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
    Calendar,
    List,
    Tag,
} from 'antd';
import {
    ArrowLeftOutlined,
    SaveOutlined,
    DeleteOutlined,
    CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import apiClient, { getFoodItems, getBudgetSettings } from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

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

    // 消費月曆相關
    const [calendarVisible, setCalendarVisible] = useState(false);
    const [wineItems, setWineItems] = useState([]);
    const [budgetSettings, setBudgetSettings] = useState(null);
    const [calendarMonth, setCalendarMonth] = useState(dayjs());
    const [selectedDate, setSelectedDate] = useState(null);
    const [dailyItems, setDailyItems] = useState([]);

    useEffect(() => {
        loadItem();
        loadWineItemsAndBudget();
    }, [id]);

    const loadItem = async () => {
        try {
            setLoading(true);
            const data = await apiClient.get(`/wine-items/${id}`);
            setItem(data);

            // 填入表單
            form.setFieldsValue({
                ...data,
                price: data.purchase_price,
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

    // 載入酒款資料和預算設定（用於月曆顯示）
    const loadWineItemsAndBudget = async () => {
        try {
            const [itemsData, budgetData] = await Promise.all([
                getFoodItems({ status: 'all' }),
                getBudgetSettings(),
            ]);
            setWineItems(itemsData.filter((item) => item.purchase_price && item.purchase_price > 0));
            setBudgetSettings(budgetData);
        } catch (error) {
            console.error('載入消費資料失敗:', error);
        }
    };

    // 計算每日消費總額
    const getDailySpending = () => {
        const dailyMap = {};
        wineItems.forEach((item) => {
            if (item.purchase_date && item.purchase_price) {
                const dateKey = dayjs(item.purchase_date).format('YYYY-MM-DD');
                if (!dailyMap[dateKey]) {
                    dailyMap[dateKey] = 0;
                }
                dailyMap[dateKey] += item.purchase_price;
            }
        });
        return dailyMap;
    };

    // 計算指定月份的消費總額
    const getMonthlyTotal = (month) => {
        const monthKey = month.format('YYYY-MM');
        return wineItems
            .filter((item) => dayjs(item.purchase_date).format('YYYY-MM') === monthKey)
            .reduce((sum, item) => sum + (item.purchase_price || 0), 0);
    };

    // 日曆單元格渲染
    const dateCellRender = (value) => {
        const dateKey = value.format('YYYY-MM-DD');
        const dailySpending = getDailySpending();
        const spending = dailySpending[dateKey];
        if (spending) {
            return (
                <div style={{
                    background: '#c9a227',
                    color: '#000',
                    borderRadius: 4,
                    padding: '2px 4px',
                    fontSize: 10,
                    textAlign: 'center',
                }}>
                    ${spending.toLocaleString()}
                </div>
            );
        }
        return null;
    };

    // 日期選擇處理 - 同步更新購買日期欄位
    const handleDateSelect = (date) => {
        setSelectedDate(date);
        const dateKey = date.format('YYYY-MM-DD');
        const items = wineItems.filter(
            (item) => dayjs(item.purchase_date).format('YYYY-MM-DD') === dateKey
        );
        setDailyItems(items);
        // 同步更新表單的購買日期
        form.setFieldsValue({ purchase_date: date });
    };

    // 開啟月曆時，同步表單的購買日期
    const handleOpenCalendar = () => {
        const currentPurchaseDate = form.getFieldValue('purchase_date');
        if (currentPurchaseDate) {
            setCalendarMonth(currentPurchaseDate);
            setSelectedDate(currentPurchaseDate);
            // 載入該日期的消費明細
            const dateKey = currentPurchaseDate.format('YYYY-MM-DD');
            const items = wineItems.filter(
                (item) => dayjs(item.purchase_date).format('YYYY-MM-DD') === dateKey
            );
            setDailyItems(items);
        }
        setCalendarVisible(true);
    };

    // 月份切換處理
    const handlePanelChange = (date) => {
        setCalendarMonth(date);
        setSelectedDate(null);
        setDailyItems([]);
    };

    // 計算選中日期的總消費
    const selectedDateTotal = dailyItems.reduce((sum, item) => sum + (item.purchase_price || 0), 0);

    // 開瓶
    const handleOpenBottle = async () => {
        try {
            const data = await apiClient.post(`/wine-items/${id}/open`);
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
            const data = await apiClient.post(`/wine-items/${id}/update-remaining?remaining=${remaining}`);
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
                    const data = await apiClient.post(`/wine-items/${id}/change-status?new_status=${newStatus}`);
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
                purchase_price: values.price,
                purchase_date: values.purchase_date?.format('YYYY-MM-DD'),
                optimal_drinking_start: values.optimal_drinking_start?.format('YYYY-MM-DD'),
                optimal_drinking_end: values.optimal_drinking_end?.format('YYYY-MM-DD'),
            };
            delete payload.price;

            await apiClient.put(`/wine-items/${id}`, payload);

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
                try {
                    await apiClient.delete(`/wine-items/${id}`);
                    message.success('已刪除');
                    navigate('/');
                } catch (error) {
                    message.error('刪除失敗');
                }
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
            <Layout style={{ minHeight: '100vh', background: '#1a1a1a' }}>
                <Content style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Spin size="large" tip="載入中..." />
                </Content>
            </Layout>
        );
    }

    return (
        <Layout style={{ minHeight: '100vh', background: '#1a1a1a' }}>
            <Content style={{ padding: '16px', maxWidth: 480, margin: '0 auto' }}>
                {/* 標題 */}
                <div style={{ marginBottom: 16 }}>
                    <Button
                        type="text"
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate('/')}
                        style={{ color: '#888' }}
                    >
                        返回
                    </Button>
                    <Title level={3} style={{ marginTop: 8, color: '#f5f5f5' }}>編輯酒款</Title>
                </div>

                {/* 圖片 */}
                {item?.image_url && (
                    <Card style={{ marginBottom: 16, textAlign: 'center', background: '#2d2d2d', border: 'none' }}>
                        <img
                            src={item.image_url}
                            alt={item.name}
                            style={{ maxWidth: '100%', maxHeight: 200, objectFit: 'contain', borderRadius: 12 }}
                        />
                    </Card>
                )}

                {/* 開瓶狀態操作 */}
                {item?.status === 'active' && (
                    <Card style={{ marginBottom: 16, background: '#2d2d2d', border: 'none' }}>
                        <Title level={5} style={{ color: '#f5f5f5' }}>🍷 開瓶狀態</Title>

                        {item.bottle_status === 'unopened' ? (
                            <Button type="primary" onClick={handleOpenBottle} block style={{ background: '#c9a227', borderColor: '#c9a227' }}>
                                開瓶
                            </Button>
                        ) : (
                            <div>
                                <Text style={{ display: 'block', marginBottom: 8, color: '#888' }}>
                                    剩餘量：{remainingLabels[item.remaining_amount]}
                                </Text>
                                <Space wrap>
                                    {remainingOptions.map((opt) => (
                                        <Button
                                            key={opt}
                                            type={item.remaining_amount === opt ? 'primary' : 'default'}
                                            onClick={() => handleUpdateRemaining(opt)}
                                            style={item.remaining_amount === opt ? { background: '#c9a227', borderColor: '#c9a227' } : {}}
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
                    <Card style={{ marginBottom: 16, background: '#2d2d2d', border: 'none' }}>
                        <Title level={5} style={{ color: '#f5f5f5' }}>📤 變更狀態</Title>
                        <Space wrap>
                            <Button onClick={() => handleChangeStatus('sold')}>標記為售出</Button>
                            <Button onClick={() => handleChangeStatus('gifted')}>標記為送禮</Button>
                            <Button onClick={() => handleChangeStatus('consumed')}>標記為喝完</Button>
                        </Space>
                    </Card>
                )}

                {/* 表單 */}
                <Form form={form} layout="vertical" onFinish={handleSubmit}>
                    <Form.Item label={<span style={{ color: '#888' }}>酒名</span>} name="name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>

                    <Form.Item label={<span style={{ color: '#888' }}>酒類</span>} name="wine_type" rules={[{ required: true }]}>
                        <Select>
                            {wineTypes.map((t) => <Option key={t} value={t}>{t}</Option>)}
                        </Select>
                    </Form.Item>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label={<span style={{ color: '#888' }}>品牌/酒莊</span>} name="brand" style={{ flex: 1 }}>
                            <Input />
                        </Form.Item>
                        <Form.Item label={<span style={{ color: '#888' }}>年份</span>} name="vintage" style={{ width: 100 }}>
                            <InputNumber style={{ width: '100%' }} />
                        </Form.Item>
                    </Space>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label={<span style={{ color: '#888' }}>產區</span>} name="region" style={{ flex: 1 }}>
                            <Input />
                        </Form.Item>
                        <Form.Item label={<span style={{ color: '#888' }}>國家</span>} name="country" style={{ flex: 1 }}>
                            <Input />
                        </Form.Item>
                    </Space>

                    <Space style={{ width: '100%' }} size="middle">
                        <Form.Item label={<span style={{ color: '#888' }}>酒精濃度 (%)</span>} name="abv" style={{ flex: 1 }}>
                            <InputNumber step={0.1} style={{ width: '100%' }} />
                        </Form.Item>
                        <Form.Item label={<span style={{ color: '#888' }}>數量</span>} name="quantity" style={{ flex: 1 }}>
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>
                    </Space>

                    <Form.Item label={<span style={{ color: '#888' }}>保存類型 (影響開瓶後建議飲用期)</span>} name="preservation_type" rules={[{ required: true }]}>
                        <Radio.Group buttonStyle="solid">
                            <Radio.Button value="immediate">即飲型 (3-5天)</Radio.Button>
                            <Radio.Button value="aging">陳年型 (較長)</Radio.Button>
                        </Radio.Group>
                    </Form.Item>

                    {/* 價格 + 日曆按鈕 */}
                    <Form.Item label={<span style={{ color: '#888' }}>價格（台幣）</span>} style={{ marginBottom: 0 }}>
                        <Space.Compact style={{ width: '100%' }}>
                            <Form.Item name="price" noStyle>
                                <InputNumber
                                    min={0}
                                    style={{ width: 'calc(100% - 40px)' }}
                                    formatter={(value) => value ? `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : ''}
                                    parser={(value) => value.replace(/,/g, '')}
                                />
                            </Form.Item>
                            <Button
                                icon={<CalendarOutlined />}
                                onClick={handleOpenCalendar}
                                title="查看本月消費"
                                style={{ width: 40 }}
                            />
                        </Space.Compact>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            點擊日曆查看本月消費紀錄
                        </Text>
                    </Form.Item>

                    {/* 購買日期 */}
                    <Form.Item label={<span style={{ color: '#888' }}>購買日期</span>} name="purchase_date" style={{ marginTop: 16 }}>
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>

                    <Form.Item label={<span style={{ color: '#888' }}>存放位置</span>} name="storage_location">
                        <Input placeholder="例：A架第2層" />
                    </Form.Item>

                    <Form.Item label={<span style={{ color: '#888' }}>備註</span>} name="notes">
                        <TextArea rows={3} placeholder="品酒筆記、特殊說明..." />
                    </Form.Item>

                    <Divider style={{ borderColor: '#404040' }} />

                    <Button
                        type="primary"
                        htmlType="submit"
                        icon={<SaveOutlined />}
                        loading={saving}
                        block
                        style={{ background: 'linear-gradient(45deg, #c9a227, #eebf38)', border: 'none', color: '#000', fontWeight: 'bold' }}
                    >
                        儲存變更
                    </Button>

                    <Button danger icon={<DeleteOutlined />} onClick={handleDelete} block style={{ marginTop: 8 }}>
                        刪除此酒款
                    </Button>
                </Form>

                {/* 消費月曆 Modal */}
                <Modal
                    title="本月消費紀錄"
                    open={calendarVisible}
                    onCancel={() => {
                        setCalendarVisible(false);
                        setSelectedDate(null);
                        setDailyItems([]);
                    }}
                    footer={null}
                    width={600}
                >
                    {/* 月份消費總計 */}
                    <Card
                        size="small"
                        style={{ marginBottom: 16, background: '#2d2d2d', border: '1px solid #404040' }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <Text strong style={{ fontSize: 16, color: '#f5f5f5' }}>
                                    {calendarMonth.format('YYYY 年 M 月')} 總消費
                                </Text>
                                <Text strong style={{ fontSize: 20, color: '#c9a227', marginLeft: 12 }}>
                                    NT$ {getMonthlyTotal(calendarMonth).toLocaleString()}
                                </Text>
                            </div>
                            {budgetSettings?.monthly_budget && (
                                <div>
                                    <Text style={{ color: '#888' }}>預算上限：</Text>
                                    <Text strong style={{ color: '#f5f5f5' }}>NT$ {budgetSettings.monthly_budget.toLocaleString()}</Text>
                                </div>
                            )}
                        </div>
                    </Card>

                    <Calendar
                        fullscreen={false}
                        cellRender={dateCellRender}
                        onSelect={handleDateSelect}
                        onPanelChange={handlePanelChange}
                    />

                    {/* 當日消費明細 */}
                    {selectedDate && (
                        <Card
                            size="small"
                            title={<span style={{ color: '#f5f5f5' }}>{selectedDate.format('YYYY/MM/DD')} 消費明細</span>}
                            style={{ marginTop: 16, background: '#2d2d2d', border: '1px solid #404040' }}
                        >
                            {dailyItems.length === 0 ? (
                                <Text style={{ color: '#888' }}>當日無消費紀錄</Text>
                            ) : (
                                <>
                                    <div style={{ marginBottom: 12 }}>
                                        <Text strong style={{ fontSize: 16, color: '#c9a227' }}>
                                            支出：NT$ {selectedDateTotal.toLocaleString()}
                                        </Text>
                                    </div>
                                    <List
                                        size="small"
                                        dataSource={dailyItems}
                                        renderItem={(listItem) => (
                                            <List.Item style={{ borderBottom: '1px solid #404040' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                                                    <Space>
                                                        <Text style={{ color: '#f5f5f5' }}>{listItem.name}</Text>
                                                        {listItem.wine_type && <Tag color="gold">{listItem.wine_type}</Tag>}
                                                    </Space>
                                                    <Text strong style={{ color: '#c9a227' }}>NT$ {listItem.purchase_price?.toLocaleString()}</Text>
                                                </div>
                                            </List.Item>
                                        )}
                                    />
                                </>
                            )}
                        </Card>
                    )}
                </Modal>
            </Content>
        </Layout>
    );
}

export default EditWineItem;
