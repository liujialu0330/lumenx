"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

interface SystemStatus {
    checked: boolean;
    ffmpegAvailable: boolean;
    recheckSystem: () => void;
}

const SystemStatusContext = createContext<SystemStatus>({
    checked: false,
    ffmpegAvailable: true,
    recheckSystem: () => {},
});

export function useSystemStatus() {
    return useContext(SystemStatusContext);
}

export default function SystemStatusProvider({ children }: { children: React.ReactNode }) {
    const [status, setStatus] = useState<{ checked: boolean; ffmpegAvailable: boolean }>({
        checked: false,
        ffmpegAvailable: true,
    });

    const doCheck = useCallback(() => {
        api.checkSystem()
            .then((data) => {
                const available = data?.dependencies?.ffmpeg?.available ?? true;
                setStatus({ checked: true, ffmpegAvailable: available });
            })
            .catch(() => {
                setStatus({ checked: true, ffmpegAvailable: false });
            });
    }, []);

    useEffect(() => {
        doCheck();
    }, [doCheck]);

    const value: SystemStatus = {
        ...status,
        recheckSystem: doCheck,
    };

    return (
        <SystemStatusContext.Provider value={value}>
            {children}
        </SystemStatusContext.Provider>
    );
}
