/**
 * 華麗動畫按鈕元件
 *
 * 金色主題的華麗動畫按鈕，用於首頁主要 CTA
 * 支援自訂文字和圖示
 */

import '../styles/PhotoUploadButton.css';

// 星星圖示（預設）
const SparkleIcon = () => (
    <svg
        className="sparkle"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
    >
        <path
            className="path"
            d="M12 3L13.2 8.8L19 10L13.2 11.2L12 17L10.8 11.2L5 10L10.8 8.8L12 3Z"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        <path
            className="path"
            d="M19 15L19.6 17.4L22 18L19.6 18.6L19 21L18.4 18.6L16 18L18.4 17.4L19 15Z"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        <path
            className="path"
            d="M5 2L5.4 3.6L7 4L5.4 4.4L5 6L4.6 4.4L3 4L4.6 3.6L5 2Z"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
    </svg>
);

// 乾杯圖示
const CheersIcon = () => (
    <span className="cheers-icon" role="img" aria-label="cheers">🥂</span>
);

function PhotoUploadButton({ onClick, text = "拍照入庫", icon = "sparkle" }) {
    return (
        <button className="photo-upload-button" onClick={onClick}>
            <span className="dots_border"></span>
            {icon === "sparkle" ? <SparkleIcon /> : <CheersIcon />}
            <span className="text_button">{text}</span>
        </button>
    );
}

export default PhotoUploadButton;
