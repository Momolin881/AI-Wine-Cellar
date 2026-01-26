/**
 * 通知設定頁面
 *
 * 允許使用者設定開瓶提醒和適飲期提醒的參數。
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Switch,
  Select,
  TimePicker,
  Button,
  message,
  Spin,
  Typography,
  Space,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  SendOutlined,
  BellOutlined,
  CalendarOutlined,
  AlertOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getNotificationSettings, updateNotificationSettings, testExpiryNotification } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const weekDays = [
  { value: 0, label: '週日' },
  { value: 1, label: '週一' },
  { value: 2, label: '週二' },
  { value: 3, label: '週三' },
  { value: 4, label: '週四' },
  { value: 5, label: '週五' },
  { value: 6, label: '週六' },
];

function NotificationSettings() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const settings = await getNotificationSettings();

      form.setFieldsValue({
        opened_reminder_enabled: settings.opened_reminder_enabled ?? true,
        expiry_warning_enabled: settings.expiry_warning_enabled,
        monthly_check_day: settings.monthly_check_day ?? 1,
        weekly_notification_day: settings.weekly_notification_day ?? 5,
        notification_time: settings.notification_time ? dayjs(settings.notification_time, 'HH:mm') : dayjs('09:00', 'HH:mm'),
      });

    } catch (error) {
      console.error('載入通知設定失敗:', error);
      message.error('載入設定失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    try {
      setSubmitting(true);

      const settings = {
        opened_reminder_enabled: values.opened_reminder_enabled,
        expiry_warning_enabled: values.expiry_warning_enabled,
        monthly_check_day: values.monthly_check_day,
        weekly_notification_day: values.weekly_notification_day,
        notification_time: values.notification_time?.format('HH:mm') || '09:00',
      };

      await updateNotificationSettings(settings);
      message.success('通知設定已儲存');

    } catch (error) {
      console.error('儲存通知設定失敗:', error);
      message.error('儲存設定失敗，請稍後再試');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTestNotification = async () => {
    try {
      setTesting(true);
      await testExpiryNotification();
      message.success('測試通知已發送，請查看 LINE 訊息');
    } catch (error) {
      console.error('發送測試通知失敗:', error);
      if (error.response?.status === 401) {
        message.error('請先在 LINE 內重新開啟應用');
      } else {
        message.error('發送測試通知失敗：' + (error.response?.data?.detail || '請稍後再試'));
      }
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        padding: '20px',
        background: '#1a1a1a',
      }}>
        <Spin size="large" tip="載入中..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', paddingBottom: '100px', backgroundColor: '#1a1a1a', minHeight: '100vh' }}>
      {/* 標題列 */}
      <div style={{ marginBottom: '20px' }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/settings')}
          style={{ marginBottom: '10px', color: '#888' }}
        >
          返回
        </Button>
        <Title level={2} style={{ margin: 0, color: '#f5f5f5' }}>
          <BellOutlined /> 通知設定
        </Title>
        <Paragraph style={{ marginTop: '8px', color: '#888' }}>
          設定您的通知偏好，我們會在適當時間提醒您
        </Paragraph>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          opened_reminder_enabled: true,
          expiry_warning_enabled: true,
          monthly_check_day: 1,
          weekly_notification_day: 5,
          notification_time: dayjs('09:00', 'HH:mm'),
        }}
      >
        {/* 開瓶後提醒設定 */}
        <Card
          title={
            <Space>
              <AlertOutlined style={{ color: '#faad14' }} />
              <span style={{ color: '#f5f5f5' }}>開瓶後提醒</span>
            </Space>
          }
          style={{ marginBottom: '16px', background: '#2d2d2d', border: 'none' }}
          headStyle={{ background: '#2d2d2d', borderBottom: '1px solid #404040' }}
          styles={{ body: { background: '#2d2d2d' } }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <Text strong style={{ color: '#f5f5f5' }}>啟用開瓶提醒</Text>
              <br />
              <Text style={{ fontSize: '12px', color: '#888' }}>
                酒款開瓶後自動提醒您盡快飲用
              </Text>
            </div>
            <Form.Item
              name="opened_reminder_enabled"
              valuePropName="checked"
              style={{ marginBottom: 0 }}
            >
              <Switch />
            </Form.Item>
          </div>

          {/* 說明區塊 */}
          <div style={{ padding: '12px', background: '#252525', borderRadius: '8px', border: '1px solid #404040' }}>
            <Text style={{ color: '#888', fontSize: '13px' }}>
              根據酒款類型自動設定提醒：
            </Text>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', color: '#aaa', fontSize: '12px' }}>
              <li>即飲型酒款：開瓶後 <Text style={{ color: '#c9a227' }}>3 天</Text> 提醒</li>
              <li>陳年型酒款：開瓶後 <Text style={{ color: '#c9a227' }}>每月</Text> 提醒</li>
            </ul>
          </div>
        </Card>

        {/* 適飲期提醒設定 */}
        <Card
          title={
            <Space>
              <CalendarOutlined style={{ color: '#c9a227' }} />
              <span style={{ color: '#f5f5f5' }}>適飲期提醒（每月檢查）</span>
            </Space>
          }
          style={{ marginBottom: '16px', background: '#2d2d2d', border: 'none' }}
          headStyle={{ background: '#2d2d2d', borderBottom: '1px solid #404040' }}
          styles={{ body: { background: '#2d2d2d' } }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <Text strong style={{ color: '#f5f5f5' }}>啟用適飲期提醒</Text>
              <br />
              <Text style={{ fontSize: '12px', color: '#888' }}>
                定期檢查酒窖中即將到達適飲期的酒款
              </Text>
            </div>
            <Form.Item
              name="expiry_warning_enabled"
              valuePropName="checked"
              style={{ marginBottom: 0 }}
            >
              <Switch />
            </Form.Item>
          </div>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.expiry_warning_enabled !== currentValues.expiry_warning_enabled
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('expiry_warning_enabled') ? (
                <>
                  <Divider style={{ borderColor: '#404040', margin: '16px 0' }} />

                  <Form.Item
                    name="monthly_check_day"
                    label={<Text style={{ color: '#888' }}>每月檢查日期</Text>}
                    style={{ marginBottom: '16px' }}
                  >
                    <Select style={{ width: 120 }}>
                      {[...Array(28)].map((_, i) => (
                        <Option key={i + 1} value={i + 1}>{i + 1} 號</Option>
                      ))}
                    </Select>
                  </Form.Item>

                  <Form.Item
                    name="weekly_notification_day"
                    label={<Text style={{ color: '#888' }}>每週通知</Text>}
                    style={{ marginBottom: '16px' }}
                  >
                    <Select style={{ width: 120 }}>
                      {weekDays.map(day => (
                        <Option key={day.value} value={day.value}>{day.label}</Option>
                      ))}
                    </Select>
                  </Form.Item>

                  <Form.Item
                    name="notification_time"
                    label={<Text style={{ color: '#888' }}>通知時間</Text>}
                    style={{ marginBottom: 0 }}
                  >
                    <TimePicker
                      format="HH:mm"
                      minuteStep={30}
                      style={{ width: 120 }}
                    />
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>
        </Card>

        {/* 測試通知按鈕 */}
        <Card
          title={
            <Space>
              <SendOutlined style={{ color: '#1890ff' }} />
              <span style={{ color: '#f5f5f5' }}>測試通知</span>
            </Space>
          }
          style={{ marginBottom: '24px', background: '#2d2d2d', border: 'none' }}
          headStyle={{ background: '#2d2d2d', borderBottom: '1px solid #404040' }}
          styles={{ body: { background: '#2d2d2d' } }}
        >
          <Paragraph style={{ marginBottom: '16px', color: '#888' }}>
            點擊下方按鈕立即發送一則測試通知到您的 LINE，確認通知功能正常運作。
          </Paragraph>
          <Button
            icon={<SendOutlined />}
            onClick={handleTestNotification}
            loading={testing}
            block
            style={{ background: '#3d3d3d', borderColor: '#555', color: '#f5f5f5' }}
          >
            發送測試通知
          </Button>
        </Card>

        {/* 儲存按鈕 */}
        <Button
          type="primary"
          htmlType="submit"
          block
          size="large"
          loading={submitting}
          style={{
            position: 'fixed',
            bottom: '20px',
            left: '20px',
            right: '20px',
            maxWidth: '440px',
            margin: '0 auto',
            zIndex: 1000,
            background: 'linear-gradient(45deg, #c9a227, #eebf38)',
            border: 'none',
            color: '#000',
            fontWeight: 'bold',
          }}
        >
          儲存設定
        </Button>
      </Form>
    </div>
  );
}

export default NotificationSettings;
