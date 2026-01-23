/**
 * 正方形酒款卡片元件
 * 
 * 顯示：酒標圖片、酒名、酒款類型、ABV、開瓶狀態
 * 用於首頁的酒款展示，一排兩張
 */

import './WineCardSquare.css';

function WineCardSquare({ item, onClick }) {
    const { name, wine_type, abv, bottle_status, image_url } = item;

    const getWineEmoji = (type) => {
        const emojiMap = {
            '紅酒': '🍷',
            '白酒': '🥂',
            '氣泡酒': '🍾',
            '香檳': '🍾',
            '威士忌': '🥃',
            '白蘭地': '🥃',
            '清酒': '🍶',
            '啤酒': '🍺',
        };
        return emojiMap[type] || '🍷';
    };

    return (
        <div className="wine-card-square" onClick={onClick}>
            <div className="wine-card-square__image-container">
                {image_url ? (
                    <img
                        src={image_url}
                        alt={name}
                        className="wine-card-square__image"
                    />
                ) : (
                    <div className="wine-card-square__placeholder">
                        {getWineEmoji(wine_type)}
                    </div>
                )}
                <span
                    className={`wine-card-square__status-badge wine-card-square__status-badge--${bottle_status}`}
                >
                    {bottle_status === 'opened' ? '已開瓶' : '未開封'}
                </span>
            </div>
            <div className="wine-card-square__info">
                <h4 className="wine-card-square__name">{name}</h4>
                <div className="wine-card-square__details">
                    <span className="wine-card-square__type">{wine_type}</span>
                    {abv && <span className="wine-card-square__abv">{abv}%</span>}
                </div>
            </div>
        </div>
    );
}

export default WineCardSquare;
