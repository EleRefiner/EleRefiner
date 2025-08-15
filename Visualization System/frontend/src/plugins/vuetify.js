import { createVuetify } from 'vuetify';
import { Ripple } from 'vuetify/directives'; // 导入 Ripple 指令
import 'vuetify/styles';

const opts = {
    directives: {
      Ripple, // 添加 Ripple 指令
    },
};

export default createVuetify(opts);
