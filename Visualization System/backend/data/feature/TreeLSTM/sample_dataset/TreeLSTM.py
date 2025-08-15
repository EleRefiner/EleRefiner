import torch
import torch.nn as nn
import torch.nn.functional as F

class TreeLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size, dropout_prob=0):
        super(TreeLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.dropout = nn.Dropout(p=dropout_prob)
        
        self.W_i = nn.Linear(input_size + hidden_size, hidden_size)
        self.W_f = nn.Linear(input_size + hidden_size, hidden_size)
        self.W_o = nn.Linear(input_size + hidden_size, hidden_size)
        self.W_u = nn.Linear(input_size + hidden_size, hidden_size)
        
    def forward(self, x, children_h, children_c):

        x = self.dropout(x)

        if children_h is None or children_h.size(0) == 0:
            if x.dim()==1:
                children_h = torch.zeros(1, self.hidden_size, device=x.device)
                children_c = torch.zeros(1, self.hidden_size, device=x.device)
            else:
                children_h = torch.zeros(*x.shape[:-1], 1, self.hidden_size, device=x.device)
                children_c = torch.zeros(*x.shape[:-1], 1, self.hidden_size, device=x.device)
        
        combined = torch.cat([x, torch.sum(children_h, dim=-2)], dim=-1)
        if x.dim()==1:
            expanded_x = x.unsqueeze(-2).expand(children_h.size(-2), x.shape[-1])
        else:
            expanded_x = x.unsqueeze(-2).expand(*x.shape[:-1], children_h.size(-2), x.shape[-1])
        children_combinded = torch.cat((expanded_x, children_h), dim=-1)

        i_t = torch.sigmoid(self.W_i(combined))
        f_t = torch.sigmoid(self.W_f(children_combinded))
        o_t = torch.sigmoid(self.W_o(combined))
        u_t = torch.tanh(self.W_u(combined))

        c = i_t * u_t + torch.sum(f_t * children_c, dim=-2)
        h = o_t * torch.tanh(c)

        return h, c


class TreeLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, dropout_prob=0):
        super(TreeLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.cell = TreeLSTMCell(input_size, hidden_size, dropout_prob)

    def forward(self, tree):

        return self._forward(tree)

    def _forward(self, node):

        children_h = []
        children_c = []
        for child in node['children']:
            child_h, child_c = self._forward(child)
            children_h.append(child_h)
            children_c.append(child_c)
        
        if len(children_h)>0:
            children_h = torch.stack(children_h)
            children_c = torch.stack(children_c)
        else:
            children_h, children_c = None, None
        
        x = node['input']
        
        h, c = self.cell(x, children_h, children_c)
        
        return h, c


class BatchTreeLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, dropout_prob=0):
        super(BatchTreeLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.cell = TreeLSTMCell(input_size, hidden_size, dropout_prob)

    def _dfs(self, node, father, ans_dict, prepared_list, cnt):
        node["bid"] = cnt[0]
        ans_dict[node["bid"]] = {"degree": -1, "ans": None, 'father': father}
        cnt[0] += 1
        if len(node['children'])==0:
            prepared_list.append(node)
            return
        ans_dict[node["bid"]]["degree"] = len(node['children'])
        for child in node['children']:
            self._dfs(child, node, ans_dict, prepared_list, cnt)

    def forward(self, node_list):

        ans_len = len(node_list)

        ans_dict = {}
        prepared_list = []
        cnt = [0]
        for node in node_list:
            self._dfs(node, None, ans_dict, prepared_list, cnt)
        
        while len(prepared_list)>0:
            device = prepared_list[0]['input'].device
            max_child_len = max([len(node['children']) for node in prepared_list])
            if max_child_len>0:
                full_children_h = torch.zeros(len(prepared_list), max_child_len, self.hidden_size, device=device)
                full_children_c = torch.zeros(len(prepared_list), max_child_len, self.hidden_size, device=device)
                for i in range(len(prepared_list)):
                    node = prepared_list[i]
                    children_h = []
                    children_c = []
                    for child in node['children']:
                        child_h, child_c = ans_dict[child["bid"]]['ans']
                        children_h.append(child_h)
                        children_c.append(child_c)
                    if len(children_h)>0:
                        children_h = torch.stack(children_h)
                        children_c = torch.stack(children_c)
                        full_children_h[i, :children_h.shape[0]] = children_h
                        full_children_c[i, :children_c.shape[0]] = children_c
            else:
                full_children_h, full_children_c = None, None
        
            full_x = []
            for i in range(len(prepared_list)):
                node = prepared_list[i]
                full_x.append(node['input'])
            full_x = torch.stack(full_x)
        
            full_h, full_c = self.cell(full_x, full_children_h, full_children_c)

            new_prepared_list = []
            for i in range(len(prepared_list)):
                node = prepared_list[i]
                ans_dict[node["bid"]]["ans"] = (full_h[i], full_c[i])
                father = ans_dict[node["bid"]]['father']
                if father is not None:
                    ans_dict[father["bid"]]["degree"] -= 1
                    if ans_dict[father["bid"]]["degree"]==0:
                        new_prepared_list.append(father)
            prepared_list = new_prepared_list
        
        h = []
        c = []
        for node in node_list:
            ans = ans_dict[node["bid"]]["ans"]
            h.append(ans[0])
            c.append(ans[1])
        
        return h, c