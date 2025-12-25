import { createContext, useContext, createSignal, type ParentProps, type Accessor } from "solid-js";

const SIDEBAR_STORAGE_KEY = "sidebar:open";

interface SidebarContextValue {
  /** 侧边栏是否展开 */
  isOpen: Accessor<boolean>;
  /** 切换侧边栏状态 */
  toggle: () => void;
  /** 设置侧边栏状态 */
  setOpen: (open: boolean) => void;
}

const SidebarContext = createContext<SidebarContextValue>();

export function SidebarProvider(props: ParentProps) {
  // 从 localStorage 读取初始状态，默认展开
  const getInitialState = () => {
    if (typeof window === "undefined") return true;
    const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY);
    return saved === null ? true : saved === "true";
  };

  const [isOpen, setIsOpen] = createSignal(getInitialState());

  const toggle = () => {
    const newState = !isOpen();
    setIsOpen(newState);
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(newState));
  };

  const setOpen = (open: boolean) => {
    setIsOpen(open);
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(open));
  };

  return (
    <SidebarContext.Provider value={{ isOpen, toggle, setOpen }}>
      {props.children}
    </SidebarContext.Provider>
  );
}

export function useSidebar(): SidebarContextValue {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}
