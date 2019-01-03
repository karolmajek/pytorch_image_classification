import torch


class LARSOptimizer(torch.optim.Optimizer):
    def __init__(self,
                 params,
                 lr,
                 momentum=0,
                 weight_decay=0,
                 eta=1e-3,
                 eps=1e-9,
                 thresh=1e-2):

        if lr < 0.0:
            raise ValueError("Invalid learning rate: {}".format(lr))
        if momentum < 0.0:
            raise ValueError("Invalid momentum value: {}".format(momentum))
        if weight_decay < 0.0:
            raise ValueError(
                "Invalid weight_decay value: {}".format(weight_decay))

        defaults = dict(
            lr=lr,
            momentum=momentum,
            weight_decay=weight_decay,
            eta=eta,
            eps=eps,
            thresh=thresh)
        super(LARSOptimizer, self).__init__(params, defaults)

    def __setstate__(self, state):
        super(LARSOptimizer, self).__setstate__(state)
        for group in self.param_groups:
            group.setdefault('nesterov', False)

    def step(self, closure=None):
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            weight_decay = group['weight_decay']
            momentum = group['momentum']
            lr = group['lr']
            eta = group['eta']
            eps = group['eps']
            thresh = group['thresh']

            for p in group['params']:
                if p.grad is None:
                    continue

                d_p = p.grad.data

                weight_norm = torch.norm(p.data)
                if weight_norm < thresh:
                    if weight_decay != 0:
                        d_p.add_(weight_decay, p.data)
                    if momentum != 0:
                        param_state = self.state[p]
                        if 'momentum_buffer' not in param_state:
                            buf = param_state[
                                'momentum_buffer'] = torch.zeros_like(p.data)
                            buf.mul_(momentum).add_(d_p)
                        else:
                            buf = param_state['momentum_buffer']
                            buf.mul_(momentum).add_(d_p)
                    p.data.add_(-lr, buf)
                else:
                    grad_norm = torch.norm(d_p)
                    local_lr = eta * weight_norm / (
                        eps + grad_norm + weight_decay * weight_norm)

                    if weight_decay != 0:
                        d_p.add_(weight_decay, p.data)
                    if momentum != 0:
                        param_state = self.state[p]
                        if 'momentum_buffer' not in param_state:
                            buf = param_state[
                                'momentum_buffer'] = torch.zeros_like(p.data)
                            buf.mul_(momentum).add_(d_p)
                        else:
                            buf = param_state['momentum_buffer']
                            buf.mul_(momentum).add_(lr * local_lr, d_p)
                    p.data.add_(-1.0, buf)

        return loss
