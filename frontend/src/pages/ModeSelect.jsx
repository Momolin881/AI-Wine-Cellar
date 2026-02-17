/**
 * Mode Select Page
 *
 * 首次使用時選擇模式：Chill vs Pro
 * 新手須完成三部曲才能解鎖 Pro Mode
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Modal } from 'antd';
import { useMode, CHILL_THEME, PRO_THEME } from '../contexts/ModeContext';
import apiClient, { getFoodItems } from '../services/api';
import '../styles/ModeSelect.css';

const { Title, Text } = Typography;

function ModeSelect() {
    const navigate = useNavigate();
    const { setMode } = useMode();
    const [questDone, setQuestDone] = useState(false);

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

    const handleSelect = (selectedMode) => {
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
        navigate('/');
    };

    return (
        <div className="mode-select">
            <div className="mode-select__header">
                <Title level={2} className="mode-select__title">
                    🍷 歡迎來到酒窖
                </Title>
                <Text className="mode-select__subtitle">
                    選擇你的風格
                </Text>
            </div>

            <div className="mode-select__cards">
                {/* Chill Mode */}
                <div
                    className="mode-card mode-card--chill"
                    onClick={() => handleSelect('chill')}
                    style={{
                        '--card-primary': CHILL_THEME.primary,
                        '--card-accent': CHILL_THEME.accent,
                        '--card-bg': CHILL_THEME.card,
                        '--card-glow': CHILL_THEME.glow,
                    }}
                >
                    <div className="mode-card__icon">🎮</div>
                    <div className="mode-card__title">Chill Mode</div>
                    <div className="mode-card__subtitle">隨興喝酒</div>
                    <ul className="mode-card__features">
                        <li>簡潔介面</li>
                        <li>快速入庫</li>
                        <li>輕鬆管理</li>
                    </ul>
                    <div className="mode-card__tag">推薦新手</div>
                </div>

                {/* Pro Mode */}
                <div
                    className={`mode-card mode-card--pro${!questDone ? ' mode-card--locked' : ''}`}
                    onClick={() => handleSelect('pro')}
                    style={{
                        '--card-primary': PRO_THEME.primary,
                        '--card-accent': PRO_THEME.accent,
                        '--card-bg': PRO_THEME.card,
                        '--card-glow': 'none',
                        opacity: questDone ? 1 : 0.5,
                    }}
                >
                    <div className="mode-card__icon">{questDone ? '🏆' : '🔒'}</div>
                    <div className="mode-card__title">Pro Mode</div>
                    <div className="mode-card__subtitle">品酒達人</div>
                    <ul className="mode-card__features">
                        <li>品飲筆記</li>
                        <li>風味標籤</li>
                        <li>詳細評分</li>
                    </ul>
                    <div className="mode-card__tag">{questDone ? '進階功能' : '完成三部曲解鎖'}</div>
                </div>
            </div>

            <Text className="mode-select__footer">
                之後可在設定中切換
            </Text>
        </div>
    );
}

export default ModeSelect;
