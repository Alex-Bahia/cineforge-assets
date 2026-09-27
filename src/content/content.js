/**
 * Content script — enables context capture from any page
 */

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_PAGE_CONTENT') {
    sendResponse({
      url: location.href,
      title: document.title,
      text: document.body?.innerText?.slice(0, 3000) || '',
      selection: window.getSelection()?.toString() || '',
      metaDescription: document.querySelector('meta[name="description"]')?.content || '',
    });
  }
  return true;
});
