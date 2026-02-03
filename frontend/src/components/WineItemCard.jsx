/**
 * 酒款卡片元件
 *
 * 顯示單一酒款資訊，支援開瓶狀態、剩餘量顯示
 * Neumorphism 深色主題
 */

import { Card, Tag, Space, Button, Popconfirm, Typography } from 'antd';
import {
    EditOutlined,
    DeleteOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

// 酒類圖標對應
const wineTypeEmoji = {
    '紅酒': '🍷',
    '白酒': '🥂',
    '氣泡酒': '🍾',
    '香檳': '🍾',
    '威士忌': '🥃',
    '白蘭地': '🥃',
    '伏特加': '🍸',
    '清酒': '🍶',
    '啤酒': '🍺',
    '其他': '🍹',
};

// 剩餘量對應百分比
const remainingPercent = {
    'full': 100,
    '3/4': 75,
    '1/2': 50,
    '1/4': 25,
    'empty': 0,
};

function WineItemCard({ item, onEdit, onDelete }) {
    const emoji = wineTypeEmoji[item.wine_type] || '🍷';

    return (
        <Card
            className="wine-card"
            style={{ marginBottom: 12 }}
            styles={{ body: { padding: 16 } }}
        >
            <div style={{ display: 'flex', gap: 12 }}>
                {/* 圖片或 Emoji */}
                <div
                    style={{
                        width: 80,
                        height: 80,
                        borderRadius: 12,
                        background: 'var(--bg-tertiary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 36,
                        overflow: 'hidden',
                        boxShadow: 'inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)',
                    }}
                >
                    {item.image_url ? (
                        <img
                            src={item.image_url}
                            alt={item.name}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            loading="lazy"
                        />
                    ) : (
                        emoji
                    )}
                </div>

                {/* 資訊 */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    {/* 名稱 */}
                    <div style={{ marginBottom: 4 }}>
                        <Text strong style={{ fontSize: 16 }}>
                            {item.name}
                        </Text>
                    </div>

                    {/* 品牌/酒莊 */}
                    {item.brand && (
                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                            {item.brand}
                        </Text>
                    )}

                    {/* 標籤 */}
                    <Space size={4} wrap style={{ marginBottom: 8 }}>
                        <Tag style={{ margin: 0 }}>{item.wine_type}</Tag>
                        {item.vintage && (
                            <Tag style={{ margin: 0 }}>{item.vintage}年</Tag>
                        )}
                        {item.region && (
                            <Tag style={{ margin: 0 }}>{item.region}</Tag>
                        )}
                        {item.abv && (
                            <Tag style={{ margin: 0 }}>{item.abv}%</Tag>
                        )}
                    </Space>

                    {/* 開瓶狀態和剩餘量 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Tag
                            color={item.bottle_status === 'unopened' ? 'green' : 'orange'}
                            style={{ margin: 0 }}
                        >
                            {item.bottle_status === 'unopened' ? '未開封' : '已開瓶'}
                        </Tag>

                        {item.bottle_status === 'opened' && (
                            <div className="remaining-indicator">
                                <div className="remaining-bar">
                                    <div
                                        className="remaining-fill"
                                        style={{ width: `${remainingPercent[item.remaining_amount] || 100}%` }}
                                    />
                                </div>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    {item.remaining_amount === 'full' ? '滿' : item.remaining_amount}
                                </Text>
                            </div>
                        )}

                        {/* 數量 */}
                        {item.quantity > 1 && (
                            <Tag color="gold" style={{ margin: 0 }}>
                                x{item.quantity}
                            </Tag>
                        )}
                    </div>

                    {/* 價格 */}
                    {item.purchase_price && (
                        <Text
                            style={{
                                fontSize: 14,
                                color: 'var(--accent-gold)',
                                fontWeight: 600,
                                display: 'block',
                                marginTop: 4,
                            }}
                        >
                            ${item.purchase_price.toLocaleString()}
                        </Text>
                    )}
                </div>

                {/* 操作按鈕 */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <Button
                        type="text"
                        icon={<EditOutlined />}
                        onClick={onEdit}
                        style={{ color: 'var(--text-secondary)' }}
                    />
                    <Popconfirm
                        title="確定要刪除這支酒嗎？"
                        onConfirm={onDelete}
                        okText="確定"
                        cancelText="取消"
                    >
                        <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                        />
                    </Popconfirm>
                </div>
            </div>
        </Card>
    );
}

export default WineItemCard;
