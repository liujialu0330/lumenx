"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { api } from "@/lib/api";

interface SystemStatus {
    checked: boolean;
    ffmpegAvailable: boolean;
}

const SystemStatusContext = createContext<SystemStatus>({
    checked: false,
    ffmpegAvailable: true,
});

export function useSystemStatus() {
    return useContext(SystemStatusContext);
}

export default function SystemStatusProvider({ children }: { children: React.ReactNode }) {
    const [status, setStatus] = useState<SystemStatus>({ checked: false, ffmpegAvailable: true });

    useEffect(() => {
        let cancelled = false;
        api.checkSystem()
            .then((data) => {
                if (cancelled) return;
                const available = data?.dependencies?.ffmpeg?.available ?? true;
                setStatus({ checked: true, ffmpegAvailable: available });
            })
            .catch(() => {
                if (cancelled) return;
                setStatus({ checked: true, ffmpegAvailable: false });
            });
        return () => { cancelled = true; };
    }, []);

    return (
        <SystemStatusContext.Provider value={status}>
            {children}
        </SystemStatusContext.Provider>
    );
}
