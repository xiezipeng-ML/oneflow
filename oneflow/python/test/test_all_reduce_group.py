import oneflow as flow

def test_variable_reduced_as_loss_on_two_device(test_case):
    flow.config.gpu_device_num(2)
    func_config = flow.function_config()
    func_config.enable_all_reduce_group(True)
    func_config.train.primary_lr(5)
    func_config.train.model_update_conf(dict(naive_conf={}))
    @flow.function(func_config)
    def Foo():
        w = flow.get_variable("w", (10,), initializer=flow.constant_initializer(100))
        y = flow.math.reduce_sum(w)
        flow.losses.add_loss(y)
        return y
    Foo().get()
