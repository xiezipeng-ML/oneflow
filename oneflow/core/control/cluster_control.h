#ifndef ONEFLOW_CORE_CONTROL_CLUSTER_CONTROL_H_
#define ONEFLOW_CORE_CONTROL_CLUSTER_CONTROL_H_

namespace oneflow {

struct ClusterControl final {
  static void MasterSendSessionStart();
  static void MasterSendHaltAndWaitAck();
  static void WorkerSendAckAndExitIfReceiveHalt();
};

}  // namespace oneflow

#endif  // ONEFLOW_CORE_CONTROL_CLUSTER_CONTROL_H_
