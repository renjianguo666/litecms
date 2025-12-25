/**
 * 计算分页信息
 */
export function calculatePagination(
  currentPage: number,
  pageSize: number,
  total: number,
) {
  const totalPages = Math.ceil(total / pageSize) || 1;
  const hasNext = currentPage < totalPages;
  const hasPrev = currentPage > 1;
  const startIndex = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, total);

  return {
    totalPages,
    hasNext,
    hasPrev,
    startIndex,
    endIndex,
    showingText: total === 0 
      ? '暂无数据' 
      : `显示 ${startIndex}-${endIndex} 条，共 ${total} 条记录`,
  };
}

/**
 * 简单的 cn 工具函数（合并 class）
 */
export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
