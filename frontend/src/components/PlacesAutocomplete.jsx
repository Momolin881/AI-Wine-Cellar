import React, { useEffect, useRef, useState } from 'react';
import { Input } from 'antd';
import { EnvironmentOutlined } from '@ant-design/icons';
import { Loader } from '@googlemaps/js-api-loader';

const PlacesAutocomplete = ({ 
    value, 
    onChange, 
    onPlaceSelect, 
    placeholder = "輸入地點...", 
    style,
    theme
}) => {
    const inputRef = useRef(null);
    const autocompleteRef = useRef(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const loader = new Loader({
            apiKey: import.meta.env.VITE_GOOGLE_PLACES_API_KEY,
            version: 'weekly',
            libraries: ['places']
        });

        loader.load().then(() => {
            setIsLoaded(true);
        }).catch(err => {
            console.error('Google Maps API failed to load:', err);
        });
    }, []);

    useEffect(() => {
        if (isLoaded && inputRef.current && !autocompleteRef.current) {
            // 初始化 Places Autocomplete
            autocompleteRef.current = new window.google.maps.places.Autocomplete(
                inputRef.current.input,
                {
                    fields: ['place_id', 'name', 'formatted_address', 'geometry'],
                    types: ['establishment', 'geocode']
                }
            );

            // 監聽地點選擇事件
            autocompleteRef.current.addListener('place_changed', () => {
                const place = autocompleteRef.current.getPlace();
                
                if (place && place.geometry) {
                    const placeData = {
                        name: place.name || '',
                        formatted_address: place.formatted_address || '',
                        place_id: place.place_id || '',
                        location: {
                            lat: place.geometry.location.lat(),
                            lng: place.geometry.location.lng()
                        }
                    };
                    
                    // 更新顯示的文字
                    const displayText = place.name || place.formatted_address || '';
                    onChange(displayText);
                    
                    // 通知父組件地點詳細資料
                    if (onPlaceSelect) {
                        onPlaceSelect(placeData);
                    }
                }
            });
        }
    }, [isLoaded, onChange, onPlaceSelect]);

    const handleInputChange = (e) => {
        onChange(e.target.value);
    };

    return (
        <Input
            ref={inputRef}
            value={value}
            onChange={handleInputChange}
            prefix={<EnvironmentOutlined style={{ color: '#888' }} />}
            placeholder={isLoaded ? placeholder : "載入 Google Maps..."}
            style={style}
            disabled={!isLoaded}
        />
    );
};

export default PlacesAutocomplete;