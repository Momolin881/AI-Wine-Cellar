
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import liff from '@line/liff';

import {
    Layout,
    Typography,
    Form,
    Input,
    DatePicker,
    Button,
    Card,
    Row,
    Col,
    Checkbox,
    message,
    Spin,
    Upload, // Import Upload
    Modal,
    Space
} from 'antd';
import {
    CalendarOutlined,
    EnvironmentOutlined,
    UserOutlined,
    UploadOutlined // Import Icon
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getFoodItems, createInvitation, getInvitationFlex, uploadInvitationImage } from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

const CreateInvitation = () => {
    const navigate = useNavigate();
    const [form] = Form.useForm();
    const [availableWines, setAvailableWines] = useState([]);
    const [selectedWines, setSelectedWines] = useState([]);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [previewVisible, setPreviewVisible] = useState(false);
    const [previewData, setPreviewData] = useState(null);
    const [customImageUrl, setCustomImageUrl] = useState(null);
    const [uploadingImage, setUploadingImage] = useState(false);

    // Initial values: Default to tomorrow, rounded to next hour? Or just tomorrow same time.
    // User asked for "Today + 1", let's do tomorrow at the start of next hour
    const tomorrow = dayjs().add(1, 'day').startOf('hour');
    const initialValues = {
        title: '',
        event_time: tomorrow,
        location: '',
        description: '',
    };

    // Fetch wines from backend
    useEffect(() => {
        const fetchWines = async () => {
            try {
                setLoading(true);
                // Use api client which handles Auth and Base URL
                const data = await getFoodItems({ status: 'active' });

                if (Array.isArray(data)) {
                    setAvailableWines(data);
                } else {
                    setAvailableWines([]);
                }
            } catch (err) {
                console.error("Failed to fetch wines", err);
                message.error("無法載入您的酒窖資料，請確認您已登入");
                // Do not fallback to mock data to avoid confusion
            } finally {
                setLoading(false);
            }
        };
        fetchWines();
    }, []);

    const handleWineToggle = (wineId) => {
        setSelectedWines(prev => {
            if (prev.includes(wineId)) {
                return prev.filter(id => id !== wineId);
            } else {
                return [...prev, wineId];
            }
        });
    };

    // Image upload handler
    const handleImageUpload = async (file) => {
        setUploadingImage(true);
        try {
            const result = await uploadInvitationImage(file);
            setCustomImageUrl(result.url);
            message.success("圖片上傳成功！");
        } catch (error) {
            console.error(error);
            message.error("圖片上傳失敗，請稍後再試");
        } finally {
            setUploadingImage(false);
        }
        return false; // Prevent auto upload by antd
    };

    const handlePreview = async () => {
        try {
            const values = await form.validateFields();
            // 取得選中酒款的名稱
            const selectedWineNames = availableWines
                .filter(wine => selectedWines.includes(wine.id))
                .map(wine => wine.name);
            setPreviewData({
                ...values,
                wineCount: selectedWines.length,
                wineNames: selectedWineNames,
                theme_image_url: customImageUrl || 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
            });
            setPreviewVisible(true);
        } catch (error) {
            console.log('Validation Failed:', error);
        }
    };

    const handleRealShare = async () => {
        setSubmitting(true);
        try {
            // 1. Call Backend API to create invitation
            const payload = {
                title: previewData.title,
                event_time: previewData.event_time.toISOString(), // Antd DatePicker returns dayjs object
                location: previewData.location,
                description: previewData.description,
                wine_ids: selectedWines,
                // TODO: Allow user to upload theme image or select from presets
                theme_image_url: previewData.theme_image_url
            };

            const data = await createInvitation(payload);
            const invitationId = data.id;

            // 2. Fetch generated Flex Message
            const flexMessage = await getInvitationFlex(invitationId);

            // 3. Use LIFF shareTargetPicker to send message
            console.log("Checking shareTargetPicker support...");
            const isInClient = liff.isInClient();
            const isApiAvailable = liff.isApiAvailable('shareTargetPicker');

            console.log(`LIFF Environment: Client=${isInClient}, API=${isApiAvailable}`);

            // 检查是否在 LINE App 内
            if (!isInClient) {
                console.warn("Not in LINE App - shareTargetPicker may not work properly");
                // 在外部浏览器中，给用户一个提示
                const proceed = window.confirm(
                    "⚠️ 偵測到您是在外部瀏覽器中使用\n\n" +
                    "shareTargetPicker 在外部瀏覽器可能無法正常發送訊息。\n" +
                    "建議您：\n" +
                    "1. 在 LINE App 中開啟此頁面\n" +
                    "2. 或使用「複製連結」功能手動分享\n\n" +
                    "點擊「確定」繼續嘗試發送，點擊「取消」複製連結"
                );

                if (!proceed) {
                    // 提供複製連結的方式
                    const invitationLink = `https://liff.line.me/${import.meta.env.VITE_LIFF_ID}/invitation/${invitationId}`;
                    try {
                        await navigator.clipboard.writeText(invitationLink);
                        message.success("連結已複製！請手動分享給朋友");
                    } catch (clipboardErr) {
                        // Fallback: 显示链接让用户手动复制
                        prompt("請複製以下連結分享:", invitationLink);
                    }
                    setSubmitting(false);
                    return;
                }
            }

            if (isApiAvailable) {
                try {
                    console.log("Attempting to open shareTargetPicker");
                    console.log("Flex Message to send:", JSON.stringify(flexMessage, null, 2));

                    // Close modal before opening picker to avoid UI clutter
                    setPreviewVisible(false);

                    // 測試模式：使用簡單文字消息
                    const testMode = window.location.search.includes('test=1');
                    let messageToSend;

                    if (testMode) {
                        // 簡單文字消息測試
                        messageToSend = [{
                            type: "text",
                            text: `🍷 品酒邀請測試\n\n${previewData.title}\n📅 ${previewData.event_time.format('YYYY-MM-DD HH:mm')}\n📍 ${previewData.location || '待定'}`
                        }];
                        console.log("使用測試模式：發送純文字消息");
                    } else {
                        messageToSend = [flexMessage];
                    }

                    const res = await liff.shareTargetPicker(messageToSend);

                    // 详细记录返回值
                    console.log("shareTargetPicker result:", res);
                    console.log("shareTargetPicker result type:", typeof res);
                    console.log("shareTargetPicker result JSON:", JSON.stringify(res));

                    // 根据 LINE 文档，成功发送后 res.status = 'success'
                    if (res) {
                        if (res.status === 'success') {
                            console.log("发送成功！");
                            message.success("邀請已成功發送！");
                            setTimeout(() => navigate('/'), 2000);
                        } else {
                            // 有返回值但不是 success
                            console.log("收到返回值但状态非 success:", res);
                            message.info(`發送結果: ${res.status || '未知'}`);
                        }
                    } else {
                        // User cancelled picking (res is undefined)
                        console.log("用户取消了选择");
                        message.info("您取消了發送邀請。");
                    }
                } catch (pickerError) {
                    console.error("shareTargetPicker error:", pickerError);
                    console.error("Error details:", {
                        code: pickerError.code,
                        message: pickerError.message,
                        stack: pickerError.stack
                    });

                    // Show explicit error to user for debugging
                    alert(`發送失敗: ${pickerError.code || pickerError.message}\n請確認 LINE App 為最新版本，且已允許傳訊權限。`);

                    // Fallback
                    message.success("建立成功！請手動複製連結分享");
                }
            } else {
                // Fallback: Copy link
                // Diagnostic alert for the user to tell us what happened
                if (isInClient) {
                    alert("您的 LINE 版本似乎不支援或未開啟 'shareTargetPicker' 權限。\n請檢查 LINE Developers Console 的設定。");
                }
                setPreviewVisible(false);
                message.success("建立成功 (手動模式)！請複製連結分享");
                // navigate(`/invitation/${data.id}`);
            }

        } catch (err) {
            console.error(err);
            message.error(err.message || "建立失敗，請稍後再試");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Layout style={{ minHeight: '100vh', background: '#1a1a1a' }}>
            <Content style={{ padding: '24px', maxWidth: 600, margin: '0 auto' }}>
                <Title level={3} style={{ color: '#c9a227', marginBottom: 24, textAlign: 'center' }}>
                    發起品飲聚會 🥂
                </Title>

                <Form
                    form={form}
                    layout="vertical"
                    initialValues={initialValues}
                    // onFinish={handleFinish} // Removed onFinish from Form
                    style={{ color: '#fff' }}
                >
                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>聚會標題</span>}
                        name="title"
                        rules={[{ required: true, message: '請輸入標題' }]}
                    >
                        <Input
                            placeholder="例如：週末品酒會"
                            style={{ background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                        />
                    </Form.Item>

                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>時間</span>}
                        name="event_time"
                        rules={[{ required: true, message: '請選擇時間' }]}
                    >
                        <DatePicker
                            showTime={{ format: 'HH:mm', minuteStep: 15 }}
                            format="YYYY-MM-DD HH:mm"
                            style={{ width: '100%', background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                            styles={{ popup: { background: '#2d2d2d' } }}
                            placeholder="選擇聚會時間"
                        />
                    </Form.Item>

                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>地點</span>}
                        name="location"
                    >
                        <Input
                            prefix={<EnvironmentOutlined style={{ color: '#888' }} />}
                            placeholder="輸入地點"
                            style={{ background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                        />
                    </Form.Item>

                    <Form.Item
                        label={<span style={{ color: '#aaa' }}>備註</span>}
                        name="description"
                    >
                        <TextArea
                            rows={3}
                            placeholder="有什麼想對朋友說的..."
                            style={{ background: '#2d2d2d', border: '1px solid #444', color: '#fff' }}
                        />
                    </Form.Item>

                    <Typography.Text strong style={{ color: '#c9a227', display: 'block', margin: '24px 0 12px' }}>
                        選擇今日酒單 ({selectedWines.length})
                    </Typography.Text>

                    {loading ? <Spin /> : (
                        <Row gutter={[16, 16]}>
                            {availableWines.length > 0 ? availableWines.map(wine => (
                                <Col span={12} key={wine.id}>
                                    <div
                                        onClick={() => handleWineToggle(wine.id)}
                                        style={{
                                            position: 'relative',
                                            cursor: 'pointer',
                                            borderRadius: 8,
                                            overflow: 'hidden',
                                            border: selectedWines.includes(wine.id) ? '2px solid #c9a227' : '2px solid transparent'
                                        }}
                                    >
                                        <div style={{ height: 120, background: '#2d2d2d', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <img
                                                src={wine.image_url || 'https://via.placeholder.com/100'}
                                                alt={wine.name}
                                                style={{ maxHeight: '90%', maxWidth: '90%', objectFit: 'contain' }}
                                            />
                                        </div>
                                        <div style={{ padding: 8, background: '#333' }}>
                                            <Text ellipsis style={{ color: '#fff', width: '100%', display: 'block' }}>{wine.name}</Text>
                                        </div>
                                        {selectedWines.includes(wine.id) && (
                                            <div style={{ position: 'absolute', top: 5, right: 5, background: '#c9a227', borderRadius: '50%', width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                ✓
                                            </div>
                                        )}
                                    </div>
                                </Col>
                            )) : (
                                <Col span={24}>
                                    <div style={{ padding: 20, textAlign: 'center', color: '#666', background: '#2d2d2d', borderRadius: 8 }}>
                                        您的酒窖目前沒有在庫酒款
                                    </div>
                                </Col>
                            )}
                        </Row>
                    )}

                    <div style={{ margin: '24px 0' }}>
                        <Typography.Text strong style={{ color: '#c9a227', display: 'block', marginBottom: 12 }}>
                            自訂邀請卡封面 (選填)
                        </Typography.Text>
                        <Upload
                            beforeUpload={handleImageUpload}
                            showUploadList={false}
                            maxCount={1}
                        >
                            <Button
                                icon={uploadingImage ? <Spin /> : <UploadOutlined />}
                                style={{ background: '#2d2d2d', borderColor: '#444', color: '#ccc', width: '100%' }}
                            >
                                {uploadingImage ? "上傳中..." : "上傳照片"}
                            </Button>
                        </Upload>
                        {customImageUrl && (
                            <div style={{ marginTop: 12, position: 'relative' }}>
                                <img src={customImageUrl} alt="Preview" style={{ width: '100%', borderRadius: 8, maxHeight: 200, objectFit: 'cover' }} />
                                <Button
                                    size="small"
                                    type="text"
                                    danger
                                    style={{ position: 'absolute', top: 5, right: 5, background: 'rgba(0,0,0,0.5)' }}
                                    onClick={(e) => { e.stopPropagation(); setCustomImageUrl(null); }}
                                >
                                    移除
                                </Button>
                            </div>
                        )}
                    </div>


                    <Button
                        type="primary"
                        onClick={handlePreview} // Changed from htmlType="submit" to onClick
                        block
                        size="large"
                        style={{ marginTop: 40, height: 50, borderRadius: 25, background: '#c9a227', borderColor: '#c9a227', color: '#000', fontWeight: 'bold' }}
                    >
                        預覽邀請卡
                    </Button>
                </Form>

                {/* Preview Modal */}
                <Modal
                    title="邀請卡預覽"
                    open={previewVisible}
                    onCancel={() => setPreviewVisible(false)}
                    footer={[
                        <Button key="back" onClick={() => setPreviewVisible(false)}>
                            修改
                        </Button>,
                        <Button key="submit" type="primary" loading={submitting} onClick={handleRealShare} style={{ background: '#06c755', borderColor: '#06c755' }}>
                            確認並發送 (LINE)
                        </Button>,
                    ]}
                    styles={{ body: { padding: 0 } }}
                >
                    {previewData && (
                        <div style={{ padding: 20, background: '#f0f0f0' }}>
                            {/* Simulate Flex Message Bubble */}
                            <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
                                <div style={{ width: '100%', paddingTop: '65%', position: 'relative' }}>
                                    <img
                                        src={previewData.theme_image_url}
                                        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                                        alt="Header"
                                    />
                                </div>
                                <div style={{ padding: '16px' }}>
                                    <div style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 8, color: '#1a1a1a' }}>{previewData.title}</div>
                                    <Space direction="vertical" size={2} style={{ color: '#666', fontSize: 13 }}>
                                        <div>📅 {previewData.event_time.format('YYYY-MM-DD HH:mm')}</div>
                                        <div>📍 {previewData.location || "地點待定"}</div>
                                        {previewData.wineNames && previewData.wineNames.length > 0 && (
                                            <div>🍷 {previewData.wineNames.join('、')}</div>
                                        )}
                                    </Space>
                                    <div style={{ marginTop: 16 }}>
                                        <Button block type="text" style={{ color: '#42659a' }}>查看詳情</Button>
                                    </div>
                                </div>
                            </div>
                            <div style={{ textAlign: 'center', marginTop: 10, color: '#999', fontSize: 12 }}>
                                * 圖片僅供參考，實際發送樣式以 LINE 為準
                            </div>
                        </div>
                    )}
                </Modal>
            </Content>
        </Layout>
    );
};

export default CreateInvitation;
