import {
  Box,
  CircuitBoard,
  Cpu,
  Fan,
  HardDrive,
  MemoryStick,
  Network,
  Package,
  Plug,
  Server,
  type LucideIcon,
} from "lucide-react";

export const CATEGORY_NAMES: Record<string, string> = {
  "164": "CPU",
  "1244": "MOTHERBOARD",
  "27386": "GRAPHICS",
  "170083": "MEMORY",
  "42014": "CHASSIS",
  "42006": "PSU",
  "42007": "COOLING",
  "51167": "NETWORK",
  "56083": "STORAGE",
};

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  "164": Cpu,
  "1244": CircuitBoard,
  "27386": Box,
  "170083": MemoryStick,
  "42014": Server,
  "42006": Plug,
  "42007": Fan,
  "51167": Network,
  "56083": HardDrive,
};

interface CategoryIconProps {
  categoryId: string | null | undefined;
  className?: string;
}

export function CategoryIcon({ categoryId, className }: CategoryIconProps) {
  const Icon = (categoryId && CATEGORY_ICONS[categoryId]) || Package;
  return <Icon className={className} strokeWidth={1.5} aria-hidden="true" />;
}
