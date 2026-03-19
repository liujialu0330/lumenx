"use client";

import { useState, useEffect } from "react";
import { X, Save, Settings, ChevronDown, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";

interface EnvConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  isRequired?: boolean;
}

interface EnvConfig {
  DASHSCOPE_API_KEY: string;
  ALIBABA_CLOUD_ACCESS_KEY_ID: string;
  ALIBABA_CLOUD_ACCESS_KEY_SECRET: string;
  OSS_BUCKET_NAME: string;
  OSS_ENDPOINT: string;
  OSS_BASE_PATH: string;
  ARK_API_KEY: string;
  KLING_ACCESS_KEY: string;
  KLING_SECRET_KEY: string;
  VIDU_API_KEY: string;
  VOLC_TTS_APPID: string;
  VOLC_TTS_TOKEN: string;
  endpoint_overrides: Record<string, string>;
  [key: string]: string | Record<string, string>;
}

const ENDPOINT_PROVIDERS = [
  { key: "DASHSCOPE_BASE_URL", label: "DashScope", placeholder: "https://dashscope.aliyuncs.com" },
  { key: "ARK_BASE_URL", label: "ARK (豆包)", placeholder: "https://ark.cn-beijing.volces.com/api/v3" },
  { key: "KLING_BASE_URL", label: "Kling", placeholder: "https://api-beijing.klingai.com/v1" },
  { key: "VIDU_BASE_URL", label: "Vidu", placeholder: "https://api.vidu.cn/ent/v2" },
];

export default function EnvConfigDialog({ isOpen, onClose, isRequired = false }: EnvConfigDialogProps) {
  const [config, setConfig] = useState<EnvConfig>({
    DASHSCOPE_API_KEY: "",
    ALIBABA_CLOUD_ACCESS_KEY_ID: "",
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: "",
    OSS_BUCKET_NAME: "",
    OSS_ENDPOINT: "",
    OSS_BASE_PATH: "",
    ARK_API_KEY: "",
    KLING_ACCESS_KEY: "",
    KLING_SECRET_KEY: "",
    VIDU_API_KEY: "",
    VOLC_TTS_APPID: "",
    VOLC_TTS_TOKEN: "",
    endpoint_overrides: {},
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [endpointsOpen, setEndpointsOpen] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const data = await api.getEnvConfig();
      setConfig({ ...config, ...data, endpoint_overrides: data.endpoint_overrides ?? {} });
    } catch (error) {
      console.error("Failed to load env config:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.saveEnvConfig(config);
      alert("配置保存成功！");
      onClose();
    } catch (error) {
      console.error("Failed to save env config:", error);
      alert("保存配置失败,请重试");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key: keyof EnvConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleEndpointChange = (envKey: string, value: string) => {
    setConfig((prev) => ({
      ...prev,
      endpoint_overrides: { ...prev.endpoint_overrides, [envKey]: value },
    }));
  };

  const canClose = true;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <Settings className="text-primary" size={24} />
            <div>
              <h2 className="text-xl font-bold text-white">环境变量配置</h2>
              <p className="text-sm text-gray-400">配置 AI 模型服务的访问凭证</p>
            </div>
          </div>
          {canClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="text-gray-400 mt-4">加载配置中...</p>
            </div>
          ) : (
            <>
              {/* DashScope API Key */}
              <div>
                <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                  <span>DashScope API Key</span>
                  <span className="text-gray-500 font-normal">例: sk-xxx</span>
                </label>
                <input
                  type="password"
                  value={config.DASHSCOPE_API_KEY}
                  onChange={(e) => handleChange("DASHSCOPE_API_KEY", e.target.value)}
                  placeholder="用于通义千问等模型"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                />
              </div>

              {/* Alibaba Cloud Access Keys */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-4">
                <p className="text-sm text-gray-400 mb-2">用于 OSS 存储服务</p>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    阿里云 Access Key ID
                  </label>
                  <input
                    type="password"
                    value={config.ALIBABA_CLOUD_ACCESS_KEY_ID}
                    onChange={(e) => handleChange("ALIBABA_CLOUD_ACCESS_KEY_ID", e.target.value)}
                    placeholder="LTAI5t..."
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    阿里云 Access Key Secret
                  </label>
                  <input
                    type="password"
                    value={config.ALIBABA_CLOUD_ACCESS_KEY_SECRET}
                    onChange={(e) => handleChange("ALIBABA_CLOUD_ACCESS_KEY_SECRET", e.target.value)}
                    placeholder="阿里云访问密钥"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              {/* OSS Configuration */}
              <div className="pt-4 border-t border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">OSS 配置</h3>
                  <a
                    href="https://oss.console.aliyun.com/overview"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:text-primary/80 transition-colors"
                  >
                    打开 OSS 控制台 →
                  </a>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                      <span>OSS Bucket Name</span>
                      <span className="text-gray-500 font-normal">例: my-comic-bucket</span>
                    </label>
                    <input
                      type="text"
                      value={config.OSS_BUCKET_NAME}
                      onChange={(e) => handleChange("OSS_BUCKET_NAME", e.target.value)}
                      placeholder="your_bucket_name"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                      <span>OSS Endpoint</span>
                      <span className="text-gray-500 font-normal">例: oss-cn-hangzhou.aliyuncs.com</span>
                    </label>
                    <input
                      type="text"
                      value={config.OSS_ENDPOINT}
                      onChange={(e) => handleChange("OSS_ENDPOINT", e.target.value)}
                      placeholder="oss-cn-beijing.aliyuncs.com"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                      <span>OSS Base Path</span>
                      <span className="text-gray-500 font-normal">例: lumenx</span>
                    </label>
                    <input
                      type="text"
                      value={config.OSS_BASE_PATH}
                      onChange={(e) => handleChange("OSS_BASE_PATH", e.target.value)}
                      placeholder="lumenx"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>
              </div>

              {/* Doubao / 火山引擎 ARK Configuration */}
              <div className="pt-4 border-t border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">豆包 / 火山引擎配置</h3>
                  <span className="text-xs text-gray-500">可选 - 用于豆包模型（LLM / 图像 / 视频）</span>
                </div>

                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-4">
                  <div>
                    <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                      <span>ARK API Key</span>
                      <span className="text-gray-500 font-normal">火山引擎 ARK 平台密钥</span>
                    </label>
                    <input
                      type="password"
                      value={config.ARK_API_KEY}
                      onChange={(e) => handleChange("ARK_API_KEY", e.target.value)}
                      placeholder="用于豆包 LLM / SeeDream / SeeDance"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>
              </div>

              {/* 火山引擎 TTS Configuration */}
              <div className="pt-4 border-t border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">火山引擎 TTS 配置</h3>
                  <span className="text-xs text-gray-500">可选 - 用于豆包语音合成</span>
                </div>

                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      TTS App ID
                    </label>
                    <input
                      type="text"
                      value={config.VOLC_TTS_APPID}
                      onChange={(e) => handleChange("VOLC_TTS_APPID", e.target.value)}
                      placeholder="火山引擎语音合成应用 ID"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      TTS Access Token
                    </label>
                    <input
                      type="password"
                      value={config.VOLC_TTS_TOKEN}
                      onChange={(e) => handleChange("VOLC_TTS_TOKEN", e.target.value)}
                      placeholder="火山引擎语音合成 Access Token"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>
              </div>

              {/* Kling Configuration */}
              <div className="pt-4 border-t border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Kling AI 配置</h3>
                  <span className="text-xs text-gray-500">可选 - 用于 Kling 视频生成</span>
                </div>

                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Kling Access Key
                    </label>
                    <input
                      type="password"
                      value={config.KLING_ACCESS_KEY}
                      onChange={(e) => handleChange("KLING_ACCESS_KEY", e.target.value)}
                      placeholder="Kling API Access Key"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Kling Secret Key
                    </label>
                    <input
                      type="password"
                      value={config.KLING_SECRET_KEY}
                      onChange={(e) => handleChange("KLING_SECRET_KEY", e.target.value)}
                      placeholder="Kling API Secret Key"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>
              </div>

              {/* Vidu Configuration */}
              <div className="pt-4 border-t border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Vidu AI 配置</h3>
                  <span className="text-xs text-gray-500">可选 - 用于 Vidu 视频生成</span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Vidu API Key
                  </label>
                  <input
                    type="password"
                    value={config.VIDU_API_KEY}
                    onChange={(e) => handleChange("VIDU_API_KEY", e.target.value)}
                    placeholder="Vidu API Key"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              {/* Advanced: API Endpoints */}
              <div className="pt-4 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setEndpointsOpen(!endpointsOpen)}
                  aria-expanded={endpointsOpen}
                  className="flex items-center gap-2 text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors"
                >
                  {endpointsOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  高级选项: API 端点
                </button>

                {endpointsOpen && (
                  <div className="mt-4 space-y-4">
                    <p className="text-xs text-gray-500">
                      自定义 API 端点地址，留空则使用默认值。海外部署时可切换到国际端点。
                    </p>
                    {ENDPOINT_PROVIDERS.map(({ key, label, placeholder }) => (
                      <div key={key}>
                        <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                          <span>{label} Base URL</span>
                          <span className="text-gray-600 font-normal text-xs">{placeholder}</span>
                        </label>
                        <input
                          type="text"
                          value={config.endpoint_overrides[key] || ""}
                          onChange={(e) => handleEndpointChange(key, e.target.value)}
                          placeholder={placeholder}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary text-sm"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-800">
          {canClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              取消
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={16} />
            {saving ? "保存中..." : "保存配置"}
          </button>
        </div>
      </div>
    </div>
  );
}
