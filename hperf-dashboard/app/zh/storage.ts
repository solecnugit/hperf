'use client';

import { useState, useEffect } from "react";


export function useLocalStorage<T>(key: string, defaultValue: T) {
    const [value, setValue] = useState<T>(defaultValue);
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        const value = localStorage.getItem(key);

        if (value !== null) {
            setValue(JSON.parse(value) as T);
        }

        setIsInitialized(true);
    }, [key]);

    useEffect(() => {
        if (isInitialized) {
            localStorage.setItem(key, JSON.stringify(value));
        }
    }, [isInitialized, key, value]);

    return [value, setValue] as const;
}