"use client";

import { useState } from "react";
import EnvConfigDialog from "@/components/project/EnvConfigDialog";

export default function EnvConfigChecker() {
  const [isEnvDialogOpen, setIsEnvDialogOpen] = useState(false);

  return (
    <EnvConfigDialog
      isOpen={isEnvDialogOpen}
      onClose={() => {
        setIsEnvDialogOpen(false);
      }}
    />
  );
}
