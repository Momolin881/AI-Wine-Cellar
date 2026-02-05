/**
 * Mode Select Page
 *
 * 首次使用時選擇模式：Chill vs Pro
 */

import { useNavigate } from 'react-router-dom';
import { Typography } from 'antd';
import { useMode, CHILL_THEME, PRO_THEME } from '../contexts/ModeContext';
import '../styles/ModeSelect.css';

const { Title, Text } = Typography;

function ModeSelect() {
    const navigate = useNavigate();
    const { setMode } = useMode();

    const handleSelect = (selectedMode) => {
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
                    className="mode-card mode-card--pro"
                    onClick={() => handleSelect('pro')}
                    style={{
                        '--card-primary': PRO_THEME.primary,
                        '--card-accent': PRO_THEME.accent,
                        '--card-bg': PRO_THEME.card,
                        '--card-glow': 'none',
                    }}
                >
                    <div className="mode-card__icon">🎯</div>
                    <div className="mode-card__title">Pro Mode</div>
                    <div className="mode-card__subtitle">品酒達人</div>
                    <ul className="mode-card__features">
                        <li>品飲筆記</li>
                        <li>風味標籤</li>
                        <li>詳細評分</li>
                    </ul>
                    <div className="mode-card__tag">進階功能</div>
                </div>
            </div>

            <Text className="mode-select__footer">
                之後可在設定中切換
            </Text>
        </div>
    );
}

export default ModeSelect;
