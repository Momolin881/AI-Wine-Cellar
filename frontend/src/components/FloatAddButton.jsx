/**
 * 浮動加號按鈕元件
 * 
 * 玻璃質感按鈕，固定於右下角
 */

import '../styles/FloatAddButton.css';

function FloatAddButton({ onClick }) {
    return (
        <button className="float-add-button" onClick={onClick}>
            <span className="wrap">
                <span className="plus-icon"></span>
            </span>
        </button>
    );
}

export default FloatAddButton;
