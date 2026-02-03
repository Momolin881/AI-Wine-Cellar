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
    Radio,
    Modal,
    Calendar,
    Badge,
    List,
    Tag,
} from 'antd';
import {
    ArrowLeftOutlined,
    CameraOutlined,
    UploadOutlined,
    SaveOutlined,
    CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

import apiClient, { getFoodItems, getBudgetSettings, matchWineHistory } from '../services/api';
import '../styles/BlobCard.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// API base URL - apiClient handles base URL, but we might need it? No, apiClient uses baseURL from .env
// We can remove manual fetch logic

const wineTypes = ['紅酒', '白酒', '粉紅酒', '氣泡酒', '香檳', '威士忌', '白蘭地', '伏特加', '清酒', '啤酒', '其他'];

function AddWineItem() {
    const navigate = useNavigate();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [recognizing, setRecognizing] = useState(false);
    const [imageUrl, setImageUrl] = useState(null);
    const [cloudinaryPublicId, setCloudinaryPublicId] = useState(null);
    const [cellars, setCellars] = useState([]);
    const [selectedCellar, setSelectedCellar] = useState(null);

    // 月曆相關狀態
    const [calendarVisible, setCalendarVisible] = useState(false);
    const [wineItems, setWineItems] = useState([]);
    const [selectedDate, setSelectedDate] = useState(null);
    const [dailyItems, setDailyItems] = useState([]);
    const [calendarMonth, setCalendarMonth] = useState(dayjs());
    const [budgetSettings, setBudgetSettings] = useState(null);

    useEffect(() => {
        loadCellars();
        loadWineItemsAndBudget();
    }, []);

    const loadCellars = async () => {
        try {
            const data = await apiClient.get('/wine-cellars');
            setCellars(data);
            if (data.length > 0) {
                // 自動選擇第一個酒窖（預設行為：一用戶一酒窖）
                const defaultCellarId = data[0].id;
                setSelectedCellar(defaultCellarId);
                form.setFieldsValue({ cellar_id: defaultCellarId });
            }
        } catch (error) {
            console.error('載入酒窖失敗:', error);
            // 如果沒有酒窖，可能需要建立一個預設的（這裡暫時略過，假設已有）
        }
    };

    // 載入酒款資料和預算設定（用於月曆顯示）
    const loadWineItemsAndBudget = async () => {
        try {
            const [itemsData, budgetData] = await Promise.all([
                // 查詢所有狀態的酒款（包含 consumed），以保留消費歷史記錄
                getFoodItems({ status: 'all' }),
                getBudgetSettings(),
            ]);
            // 只保留有價格的酒款
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
        const amount = dailySpending[dateKey];

        if (amount) {
            return (
                <div style={{ textAlign: 'center' }}>
                    <Badge
                        count={`$${amount}`}
                        style={{
                            backgroundColor: '#722ed1',
                            fontSize: '10px',
                            padding: '0 4px',
                        }}
                    />
                </div>
            );
        }
        return null;
    };

    // 點擊日期 - 同步更新購買日期欄位
    const handleDateSelect = (date) => {
        const dateKey = date.format('YYYY-MM-DD');
        const items = wineItems.filter(
            (item) => dayjs(item.purchase_date).format('YYYY-MM-DD') === dateKey
        );
        setSelectedDate(date);
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

    // 處理月曆月份切換
    const handlePanelChange = (date) => {
        setCalendarMonth(date);
        setSelectedDate(null);
        setDailyItems([]);
    };

    // 計算選中日期的總消費
    const selectedDateTotal = dailyItems.reduce((sum, item) => sum + (item.purchase_price || 0), 0);

    // AI 酒標辨識
    const handleImageUpload = async (file) => {
        // 如果還沒載入酒窖，先暫存 file 或顯示 Loading (這裡簡化：假設 loadCellars 很快)
        if (!selectedCellar && cellars.length === 0) {
            message.warning('正在載入酒窖資訊...');
            return false;
        }

        const targetCellarId = selectedCellar || (cellars.length > 0 ? cellars[0].id : null);

        if (!targetCellarId) {
            message.error('無法找到預設酒窖');
            return false;
        }

        try {
            setRecognizing(true);

            const formData = new FormData();
            formData.append('image', file);
            formData.append('cellar_id', selectedCellar);

            const data = await apiClient.post('/wine-items/recognize', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

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

            // 歷史酒款比對
            if (data.brand && data.name) {
                try {
                    const historyMatch = await matchWineHistory(data.brand, data.name);
                    if (historyMatch.matched && historyMatch.history.length > 0) {
                        const lastRecord = historyMatch.history[0];
                        Modal.confirm({
                            title: '📚 發現歷史記錄！',
                            content: (
                                <div style={{ color: '#333' }}>
                                    <p>您曾於 <strong style={{ color: '#722ed1' }}>{dayjs(lastRecord.purchase_date).format('YYYY/MM/DD')}</strong> 購入此酒。</p>
                                    {lastRecord.purchase_price && <p>價格：<strong style={{ color: '#52c41a', fontSize: 18 }}>NT$ {lastRecord.purchase_price.toLocaleString()}</strong></p>}
                                    {lastRecord.tasting_notes && <p style={{ color: '#666' }}>品飲筆記：{lastRecord.tasting_notes.substring(0, 50)}...</p>}
                                    <p style={{ marginTop: 16, fontWeight: 500 }}>是否套用歷史資訊？</p>
                                </div>
                            ),
                            okText: '套用',
                            cancelText: '不用',
                            styles: {
                                content: { background: '#f5f5f5', borderRadius: 12 },
                                header: { background: '#f5f5f5', borderBottom: '1px solid #e8e8e8' },
                                body: { background: '#f5f5f5', padding: '20px 24px' },
                                footer: { background: '#f5f5f5' },
                            },
                            onOk: () => {
                                form.setFieldsValue({
                                    purchase_price: lastRecord.purchase_price,
                                    tasting_notes: lastRecord.tasting_notes,
                                });
                                message.success('已套用歷史資訊');
                            }
                        });
                    }
                } catch (historyErr) {
                    console.warn('歷史比對失敗:', historyErr);
                }
            }
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
        const targetCellarId = selectedCellar || (cellars.length > 0 ? cellars[0].id : null);

        if (!targetCellarId) {
            message.error('無法找到預設酒窖');
            return;
        }

        try {
            setLoading(true);

            // 將 price 映射為 purchase_price
            const { price, ...restValues } = values;

            // 處理剩餘量數值對應
            let remainingString = values.remaining_amount;
            if (typeof values.remaining_amount === 'number') {
                const map = { 100: 'full', 75: '3/4', 50: '1/2', 25: '1/4', 0: 'empty' };
                remainingString = map[values.remaining_amount] || 'full';
            }

            const payload = {
                ...restValues,
                remaining_amount: remainingString,
                cellar_id: targetCellarId,
                image_url: imageUrl,
                cloudinary_public_id: cloudinaryPublicId,
                purchase_date: values.purchase_date?.format('YYYY-MM-DD'),
                optimal_drinking_start: values.optimal_drinking_start?.format('YYYY-MM-DD'),
                optimal_drinking_end: values.optimal_drinking_end?.format('YYYY-MM-DD'),
                recognized_by_ai: recognizing ? 1 : 0,
                purchase_price: price, // 前端 price 映射到後端 purchase_price
            };

            await apiClient.post('/wine-items', payload);

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

                {/* AI 辨識區塊 - Blob Card 效果 */}
                <div className="blob-card" style={{ marginBottom: 16 }}>
                    <div className="blob-card__blob"></div>
                    <div className="blob-card__blob blob-card__blob--secondary"></div>
                    <div className="blob-card__bg"></div>
                    <div className="blob-card__content">
                        {recognizing ? (
                            <div className="blob-card__loading">
                                <Spin size="large" tip="AI 辨識中..." />
                            </div>
                        ) : imageUrl ? (
                            <>
                                <img
                                    src={imageUrl}
                                    alt="酒標"
                                    className="blob-card__image"
                                    loading="lazy"
                                />
                                <div className="blob-card__buttons">
                                    <Upload
                                        accept="image/*"
                                        showUploadList={false}
                                        beforeUpload={handleImageUpload}
                                        capture="environment"
                                    >
                                        <Button icon={<CameraOutlined />}>重新拍照</Button>
                                    </Upload>
                                    <Upload
                                        accept="image/*"
                                        showUploadList={false}
                                        beforeUpload={handleImageUpload}
                                    >
                                        <Button icon={<UploadOutlined />}>重新上傳</Button>
                                    </Upload>
                                </div>
                            </>
                        ) : (
                            <>
                                <Text style={{ display: 'block', marginBottom: 16, color: '#aaa' }}>
                                    AI 自動辨識酒標
                                </Text>
                                <div className="blob-card__buttons">
                                    <Upload
                                        accept="image/*"
                                        showUploadList={false}
                                        beforeUpload={handleImageUpload}
                                        capture="environment"
                                    >
                                        <Button
                                            type="primary"
                                            icon={<CameraOutlined />}
                                            size="large"
                                            style={{ minWidth: 130 }}
                                        >
                                            拍照酒標
                                        </Button>
                                    </Upload>
                                    <Upload
                                        accept="image/*"
                                        showUploadList={false}
                                        beforeUpload={handleImageUpload}
                                    >
                                        <Button
                                            icon={<UploadOutlined />}
                                            size="large"
                                            style={{ minWidth: 130 }}
                                        >
                                            上傳酒照
                                        </Button>
                                    </Upload>
                                </div>
                            </>
                        )}
                    </div>
                </div>

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
                        preservation_type: 'immediate',
                        remaining_amount: 100,
                        purchase_date: dayjs(),
                    }}
                >
                    {/* 酒窖選擇 (隱藏，自動帶入) */}
                    <Form.Item name="cellar_id" hidden>
                        <Input />
                    </Form.Item>

                    {/* 保存類型 - 移到最上方 */}
                    <Form.Item label="保存類型 (影響開瓶後建議飲用期)" name="preservation_type" rules={[{ required: true }]}>
                        <Radio.Group buttonStyle="solid">
                            <Radio.Button value="immediate">即飲型 (3-5天)</Radio.Button>
                            <Radio.Button value="aging">陳年型 (較長)</Radio.Button>
                        </Radio.Group>
                    </Form.Item>

                    <Form.Item label="開瓶狀態" name="bottle_status">
                        <Radio.Group buttonStyle="solid">
                            <Radio.Button value="unopened">未開瓶</Radio.Button>
                            <Radio.Button value="opened">已開瓶</Radio.Button>
                        </Radio.Group>
                    </Form.Item>

                    {/* 只有在已開瓶時顯示剩餘量 */}
                    <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.bottle_status !== currentValues.bottle_status}>
                        {({ getFieldValue }) =>
                            getFieldValue('bottle_status') === 'opened' && (
                                <Form.Item label="剩餘量" name="remaining_amount">
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
                                        tooltip={{ formatter: null }}
                                        styles={{
                                            rail: { backgroundColor: '#444' },
                                            track: { backgroundColor: '#c9a227' },
                                            handle: { borderColor: '#c9a227', backgroundColor: '#c9a227' }
                                        }}
                                    />
                                </Form.Item>
                            )
                        }
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

                    {/* 價格（合併為單一欄位） + 日曆按鈕 */}
                    <Form.Item label="價格（台幣）" style={{ marginBottom: 0 }}>
                        <Space.Compact style={{ width: '100%' }}>
                            <Form.Item name="price" noStyle>
                                <InputNumber
                                    min={0}
                                    placeholder="1500"
                                    style={{ width: 'calc(100% - 40px)' }}
                                    formatter={(value) => value ? `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : ''}
                                    parser={(value) => value.replace(/,/g, '')}
                                />
                            </Form.Item>
                            <Button
                                icon={<CalendarOutlined />}
                                onClick={handleOpenCalendar}
                                title="查看/紀錄本月消費"
                                style={{ width: 40 }}
                            />
                        </Space.Compact>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            點擊日曆查看本月消費紀錄
                        </Text>
                    </Form.Item>

                    {/* 日期 */}
                    <Form.Item label="購買日期" name="purchase_date" style={{ marginTop: 16 }}>
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

                {/* 月曆 Modal */}
                <Modal
                    title={<><CalendarOutlined /> 本月消費紀錄</>}
                    open={calendarVisible}
                    onCancel={() => {
                        setCalendarVisible(false);
                        setSelectedDate(null);
                        setDailyItems([]);
                    }}
                    footer={null}
                    width={600}
                >
                    {/* 月份消費總計和預算 */}
                    <Card
                        size="small"
                        style={{ marginBottom: 16, background: '#f9f0ff', borderColor: '#d3adf7' }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <Text strong style={{ fontSize: 16 }}>
                                    {calendarMonth.format('YYYY 年 M 月')} 總消費
                                </Text>
                                <Text strong style={{ fontSize: 20, color: '#722ed1', marginLeft: 12 }}>
                                    NT$ {getMonthlyTotal(calendarMonth).toLocaleString()}
                                </Text>
                            </div>
                            {budgetSettings?.monthly_budget && (
                                <div>
                                    <Text type="secondary">預算上限：</Text>
                                    <Text strong>NT$ {budgetSettings.monthly_budget.toLocaleString()}</Text>
                                </div>
                            )}
                        </div>
                        {budgetSettings?.monthly_budget && (
                            <div style={{ marginTop: 8 }}>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    已使用 {((getMonthlyTotal(calendarMonth) / budgetSettings.monthly_budget) * 100).toFixed(1)}% 的預算
                                </Text>
                            </div>
                        )}
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
                            title={`${selectedDate.format('YYYY/MM/DD')} 消費明細`}
                            style={{ marginTop: 16 }}
                        >
                            {dailyItems.length === 0 ? (
                                <Text type="secondary">當日無消費紀錄</Text>
                            ) : (
                                <>
                                    <div style={{ marginBottom: 12 }}>
                                        <Text strong style={{ fontSize: 16, color: '#722ed1' }}>
                                            支出：NT$ {selectedDateTotal.toLocaleString()}
                                        </Text>
                                    </div>
                                    <List
                                        size="small"
                                        dataSource={dailyItems}
                                        renderItem={(item) => (
                                            <List.Item>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                                                    <Space>
                                                        <Text>{item.name}</Text>
                                                        {item.wine_type && <Tag color="purple">{item.wine_type}</Tag>}
                                                    </Space>
                                                    <Text strong>NT$ {item.purchase_price?.toLocaleString()}</Text>
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

export default AddWineItem;
