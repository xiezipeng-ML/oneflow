#ifndef ONEFLOW_CORE_COMM_NETWORK_EPOLL_SOCKET_WRITE_HELPER_H_
#define ONEFLOW_CORE_COMM_NETWORK_EPOLL_SOCKET_WRITE_HELPER_H_

#include "oneflow/core/comm_network/epoll/socket_message.h"
#include "oneflow/core/device/cpu_stream.h"

#ifdef PLATFORM_POSIX

namespace oneflow {

class SocketWriteHelper final {
 public:
  OF_DISALLOW_COPY_AND_MOVE(SocketWriteHelper);
  SocketWriteHelper() = delete;
  ~SocketWriteHelper();

  SocketWriteHelper(int sockfd, CpuStream* cpu_stream);

  void AsyncWrite(const SocketMsg& msg);

  void NotifyMeSocketWriteable();

 private:
  void WriteUntilCurMsgQueueEmptyOrSocketNotWriteable();
  void NotifyWorker();
  bool InitMsgWriteHandle();
  bool MsgHeadWriteHandle();
  bool MsgBodyWriteHandle();

  bool DoCurWrite(bool (SocketWriteHelper::*set_cur_write_done)());
  bool SetStatusWhenMsgHeadDone();
  bool SetStatusWhenMsgBodyDone();

#define MAKE_ENTRY(x, y) bool SetStatusWhen##x##MsgHeadDone();
  OF_PP_FOR_EACH_TUPLE(MAKE_ENTRY, SOCKET_MSG_TYPE_SEQ);
#undef MAKE_ENTRY

  int sockfd_;
  CpuStream* cpu_stream_;

  std::mutex cur_msg_queue_mtx_;
  std::queue<SocketMsg>* cur_msg_queue_;

  std::mutex pending_msg_queue_mtx_;
  std::queue<SocketMsg>* pending_msg_queue_;

  SocketMsg cur_msg_;
  bool (SocketWriteHelper::*cur_write_handle_)();
  const char* write_ptr_;
  size_t write_size_;
};

}  // namespace oneflow

#endif  // PLATFORM_POSIX

#endif  // ONEFLOW_CORE_COMM_NETWORK_EPOLL_SOCKET_WRITE_HELPER_H_
