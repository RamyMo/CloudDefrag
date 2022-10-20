\ Model Request2-Spread
\ LP format - for model browsing. Use MPS format to capture full model detail.
Maximize
  - 3 new_assign[vm0_2,s1] + new_assign[vm0_2,s7] - 8 new_assign[vm0_2,s8]
   + new_assign[vm0_2,w2] + new_assign[vm0_2,w6] + new_assign[vm0_2,w1]
   - 3 new_assign[vm1_2,s1] + new_assign[vm1_2,s7] - 8 new_assign[vm1_2,s8]
   + new_assign[vm1_2,w2] + new_assign[vm1_2,w6] + new_assign[vm1_2,w1]
   - 3 new_assign[vm2_2,s1] + new_assign[vm2_2,s7] - 8 new_assign[vm2_2,s8]
   + new_assign[vm2_2,w2] + new_assign[vm2_2,w6] + new_assign[vm2_2,w1]
   - 3 new_assign[vm3_2,s1] + new_assign[vm3_2,s7] - 8 new_assign[vm3_2,s8]
   + new_assign[vm3_2,w2] + new_assign[vm3_2,w6] + new_assign[vm3_2,w1]
   - new_assign[(vm0_2,vm1_2),(s1,w1)] - new_assign[(vm0_2,vm1_2),(w1,s1)]
   - new_assign[(vm0_2,vm1_2),(s1,w6)] - new_assign[(vm0_2,vm1_2),(w6,s1)]
   - new_assign[(vm0_2,vm1_2),(s7,w1)] - new_assign[(vm0_2,vm1_2),(w1,s7)]
   - new_assign[(vm0_2,vm1_2),(s8,w2)] - new_assign[(vm0_2,vm1_2),(w2,s8)]
   - new_assign[(vm0_2,vm1_2),(s8,w6)] - new_assign[(vm0_2,vm1_2),(w6,s8)]
   - new_assign[(vm1_2,vm2_2),(s1,w1)] - new_assign[(vm1_2,vm2_2),(w1,s1)]
   - new_assign[(vm1_2,vm2_2),(s1,w6)] - new_assign[(vm1_2,vm2_2),(w6,s1)]
   - new_assign[(vm1_2,vm2_2),(s7,w1)] - new_assign[(vm1_2,vm2_2),(w1,s7)]
   - new_assign[(vm1_2,vm2_2),(s8,w2)] - new_assign[(vm1_2,vm2_2),(w2,s8)]
   - new_assign[(vm1_2,vm2_2),(s8,w6)] - new_assign[(vm1_2,vm2_2),(w6,s8)]
   - new_assign[(vm2_2,vm3_2),(s1,w1)] - new_assign[(vm2_2,vm3_2),(w1,s1)]
   - new_assign[(vm2_2,vm3_2),(s1,w6)] - new_assign[(vm2_2,vm3_2),(w6,s1)]
   - new_assign[(vm2_2,vm3_2),(s7,w1)] - new_assign[(vm2_2,vm3_2),(w1,s7)]
   - new_assign[(vm2_2,vm3_2),(s8,w2)] - new_assign[(vm2_2,vm3_2),(w2,s8)]
   - new_assign[(vm2_2,vm3_2),(s8,w6)] - new_assign[(vm2_2,vm3_2),(w6,s8)]
Subject To
 s1_cpu_cap: 2 new_assign[vm1_2,s1] + 3 new_assign[vm2_2,s1]
   + 4 new_assign[vm3_2,s1] <= 10
 s1_memory_cap: 2 new_assign[vm1_2,s1] + 3 new_assign[vm2_2,s1]
   + 4 new_assign[vm3_2,s1] <= 10
 s1_storage_cap: 200 new_assign[vm1_2,s1] + 300 new_assign[vm2_2,s1]
   + 400 new_assign[vm3_2,s1] <= 1000
 s7_cpu_cap: 2 new_assign[vm1_2,s7] + 3 new_assign[vm2_2,s7]
   + 4 new_assign[vm3_2,s7] <= 3
 s7_memory_cap: 2 new_assign[vm1_2,s7] + 3 new_assign[vm2_2,s7]
   + 4 new_assign[vm3_2,s7] <= 3
 s7_storage_cap: 200 new_assign[vm1_2,s7] + 300 new_assign[vm2_2,s7]
   + 400 new_assign[vm3_2,s7] <= 300
 s8_cpu_cap: 2 new_assign[vm1_2,s8] + 3 new_assign[vm2_2,s8]
   + 4 new_assign[vm3_2,s8] <= 8
 s8_memory_cap: 2 new_assign[vm1_2,s8] + 3 new_assign[vm2_2,s8]
   + 4 new_assign[vm3_2,s8] <= 8
 s8_storage_cap: 200 new_assign[vm1_2,s8] + 300 new_assign[vm2_2,s8]
   + 400 new_assign[vm3_2,s8] <= 800
 (s1,w1)_bw_cap: 10 new_assign[(vm0_2,vm1_2),(s1,w1)]
   + 10 new_assign[(vm0_2,vm1_2),(w1,s1)]
   + 10 new_assign[(vm1_2,vm2_2),(s1,w1)]
   + 10 new_assign[(vm1_2,vm2_2),(w1,s1)]
   + 10 new_assign[(vm2_2,vm3_2),(s1,w1)]
   + 10 new_assign[(vm2_2,vm3_2),(w1,s1)] <= 90
 (s1,w6)_bw_cap: 10 new_assign[(vm0_2,vm1_2),(s1,w6)]
   + 10 new_assign[(vm0_2,vm1_2),(w6,s1)]
   + 10 new_assign[(vm1_2,vm2_2),(s1,w6)]
   + 10 new_assign[(vm1_2,vm2_2),(w6,s1)]
   + 10 new_assign[(vm2_2,vm3_2),(s1,w6)]
   + 10 new_assign[(vm2_2,vm3_2),(w6,s1)] <= 90
 (s7,w1)_bw_cap: 10 new_assign[(vm0_2,vm1_2),(s7,w1)]
   + 10 new_assign[(vm0_2,vm1_2),(w1,s7)]
   + 10 new_assign[(vm1_2,vm2_2),(s7,w1)]
   + 10 new_assign[(vm1_2,vm2_2),(w1,s7)]
   + 10 new_assign[(vm2_2,vm3_2),(s7,w1)]
   + 10 new_assign[(vm2_2,vm3_2),(w1,s7)] <= 90
 (s8,w2)_bw_cap: 10 new_assign[(vm0_2,vm1_2),(s8,w2)]
   + 10 new_assign[(vm0_2,vm1_2),(w2,s8)]
   + 10 new_assign[(vm1_2,vm2_2),(s8,w2)]
   + 10 new_assign[(vm1_2,vm2_2),(w2,s8)]
   + 10 new_assign[(vm2_2,vm3_2),(s8,w2)]
   + 10 new_assign[(vm2_2,vm3_2),(w2,s8)] <= 90
 (s8,w6)_bw_cap: 10 new_assign[(vm0_2,vm1_2),(s8,w6)]
   + 10 new_assign[(vm0_2,vm1_2),(w6,s8)]
   + 10 new_assign[(vm1_2,vm2_2),(s8,w6)]
   + 10 new_assign[(vm1_2,vm2_2),(w6,s8)]
   + 10 new_assign[(vm2_2,vm3_2),(s8,w6)]
   + 10 new_assign[(vm2_2,vm3_2),(w6,s8)] <= 90
 new_vlink_(vm0_2,vm1_2)_prop_delay:
   1e-06 new_assign[(vm0_2,vm1_2),(s1,w1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w1,s1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s1,w6)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w6,s1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s7,w1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w1,s7)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s8,w2)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w2,s8)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s8,w6)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w6,s8)] <= 1e-06
 new_vlink_(vm1_2,vm2_2)_prop_delay:
   1e-06 new_assign[(vm1_2,vm2_2),(s1,w1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w1,s1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s1,w6)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w6,s1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s7,w1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w1,s7)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s8,w2)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w2,s8)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s8,w6)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w6,s8)] <= 5e-06
 new_vlink_(vm2_2,vm3_2)_prop_delay:
   1e-06 new_assign[(vm2_2,vm3_2),(s1,w1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w1,s1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s1,w6)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w6,s1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s7,w1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w1,s7)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s8,w2)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w2,s8)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s8,w6)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w6,s8)] <= 5e-06
 new_req2_e2e_delay: 1e-06 new_assign[(vm0_2,vm1_2),(s1,w1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w1,s1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s1,w6)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w6,s1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s7,w1)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w1,s7)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s8,w2)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w2,s8)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(s8,w6)]
   + 1e-06 new_assign[(vm0_2,vm1_2),(w6,s8)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s1,w1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w1,s1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s1,w6)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w6,s1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s7,w1)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w1,s7)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s8,w2)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w2,s8)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(s8,w6)]
   + 1e-06 new_assign[(vm1_2,vm2_2),(w6,s8)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s1,w1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w1,s1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s1,w6)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w6,s1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s7,w1)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w1,s7)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s8,w2)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w2,s8)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(s8,w6)]
   + 1e-06 new_assign[(vm2_2,vm3_2),(w6,s8)] <= 0.001
 flow_cons_(vm0_2,vm1_2)_s1: - new_assign[vm0_2,s1] + new_assign[vm1_2,s1]
   + new_assign[(vm0_2,vm1_2),(s1,w1)] - new_assign[(vm0_2,vm1_2),(w1,s1)]
   + new_assign[(vm0_2,vm1_2),(s1,w6)] - new_assign[(vm0_2,vm1_2),(w6,s1)]
   = 0
 flow_cons_(vm0_2,vm1_2)_s7: - new_assign[vm0_2,s7] + new_assign[vm1_2,s7]
   + new_assign[(vm0_2,vm1_2),(s7,w1)] - new_assign[(vm0_2,vm1_2),(w1,s7)]
   = 0
 flow_cons_(vm0_2,vm1_2)_s8: - new_assign[vm0_2,s8] + new_assign[vm1_2,s8]
   + new_assign[(vm0_2,vm1_2),(s8,w2)] - new_assign[(vm0_2,vm1_2),(w2,s8)]
   + new_assign[(vm0_2,vm1_2),(s8,w6)] - new_assign[(vm0_2,vm1_2),(w6,s8)]
   = 0
 flow_cons_(vm0_2,vm1_2)_w2: - new_assign[vm0_2,w2] + new_assign[vm1_2,w2]
   - new_assign[(vm0_2,vm1_2),(s8,w2)] + new_assign[(vm0_2,vm1_2),(w2,s8)]
   = 0
 flow_cons_(vm0_2,vm1_2)_w6: - new_assign[vm0_2,w6] + new_assign[vm1_2,w6]
   - new_assign[(vm0_2,vm1_2),(s1,w6)] + new_assign[(vm0_2,vm1_2),(w6,s1)]
   - new_assign[(vm0_2,vm1_2),(s8,w6)] + new_assign[(vm0_2,vm1_2),(w6,s8)]
   = 0
 flow_cons_(vm0_2,vm1_2)_w1: - new_assign[vm0_2,w1] + new_assign[vm1_2,w1]
   - new_assign[(vm0_2,vm1_2),(s1,w1)] + new_assign[(vm0_2,vm1_2),(w1,s1)]
   - new_assign[(vm0_2,vm1_2),(s7,w1)] + new_assign[(vm0_2,vm1_2),(w1,s7)]
   = 0
 flow_cons_(vm1_2,vm2_2)_s1: - new_assign[vm1_2,s1] + new_assign[vm2_2,s1]
   + new_assign[(vm1_2,vm2_2),(s1,w1)] - new_assign[(vm1_2,vm2_2),(w1,s1)]
   + new_assign[(vm1_2,vm2_2),(s1,w6)] - new_assign[(vm1_2,vm2_2),(w6,s1)]
   = 0
 flow_cons_(vm1_2,vm2_2)_s7: - new_assign[vm1_2,s7] + new_assign[vm2_2,s7]
   + new_assign[(vm1_2,vm2_2),(s7,w1)] - new_assign[(vm1_2,vm2_2),(w1,s7)]
   = 0
 flow_cons_(vm1_2,vm2_2)_s8: - new_assign[vm1_2,s8] + new_assign[vm2_2,s8]
   + new_assign[(vm1_2,vm2_2),(s8,w2)] - new_assign[(vm1_2,vm2_2),(w2,s8)]
   + new_assign[(vm1_2,vm2_2),(s8,w6)] - new_assign[(vm1_2,vm2_2),(w6,s8)]
   = 0
 flow_cons_(vm1_2,vm2_2)_w2: - new_assign[vm1_2,w2] + new_assign[vm2_2,w2]
   - new_assign[(vm1_2,vm2_2),(s8,w2)] + new_assign[(vm1_2,vm2_2),(w2,s8)]
   = 0
 flow_cons_(vm1_2,vm2_2)_w6: - new_assign[vm1_2,w6] + new_assign[vm2_2,w6]
   - new_assign[(vm1_2,vm2_2),(s1,w6)] + new_assign[(vm1_2,vm2_2),(w6,s1)]
   - new_assign[(vm1_2,vm2_2),(s8,w6)] + new_assign[(vm1_2,vm2_2),(w6,s8)]
   = 0
 flow_cons_(vm1_2,vm2_2)_w1: - new_assign[vm1_2,w1] + new_assign[vm2_2,w1]
   - new_assign[(vm1_2,vm2_2),(s1,w1)] + new_assign[(vm1_2,vm2_2),(w1,s1)]
   - new_assign[(vm1_2,vm2_2),(s7,w1)] + new_assign[(vm1_2,vm2_2),(w1,s7)]
   = 0
 flow_cons_(vm2_2,vm3_2)_s1: - new_assign[vm2_2,s1] + new_assign[vm3_2,s1]
   + new_assign[(vm2_2,vm3_2),(s1,w1)] - new_assign[(vm2_2,vm3_2),(w1,s1)]
   + new_assign[(vm2_2,vm3_2),(s1,w6)] - new_assign[(vm2_2,vm3_2),(w6,s1)]
   = 0
 flow_cons_(vm2_2,vm3_2)_s7: - new_assign[vm2_2,s7] + new_assign[vm3_2,s7]
   + new_assign[(vm2_2,vm3_2),(s7,w1)] - new_assign[(vm2_2,vm3_2),(w1,s7)]
   = 0
 flow_cons_(vm2_2,vm3_2)_s8: - new_assign[vm2_2,s8] + new_assign[vm3_2,s8]
   + new_assign[(vm2_2,vm3_2),(s8,w2)] - new_assign[(vm2_2,vm3_2),(w2,s8)]
   + new_assign[(vm2_2,vm3_2),(s8,w6)] - new_assign[(vm2_2,vm3_2),(w6,s8)]
   = 0
 flow_cons_(vm2_2,vm3_2)_w2: - new_assign[vm2_2,w2] + new_assign[vm3_2,w2]
   - new_assign[(vm2_2,vm3_2),(s8,w2)] + new_assign[(vm2_2,vm3_2),(w2,s8)]
   = 0
 flow_cons_(vm2_2,vm3_2)_w6: - new_assign[vm2_2,w6] + new_assign[vm3_2,w6]
   - new_assign[(vm2_2,vm3_2),(s1,w6)] + new_assign[(vm2_2,vm3_2),(w6,s1)]
   - new_assign[(vm2_2,vm3_2),(s8,w6)] + new_assign[(vm2_2,vm3_2),(w6,s8)]
   = 0
 flow_cons_(vm2_2,vm3_2)_w1: - new_assign[vm2_2,w1] + new_assign[vm3_2,w1]
   - new_assign[(vm2_2,vm3_2),(s1,w1)] + new_assign[(vm2_2,vm3_2),(w1,s1)]
   - new_assign[(vm2_2,vm3_2),(s7,w1)] + new_assign[(vm2_2,vm3_2),(w1,s7)]
   = 0
 requested_vm_single_host[vm0_2]: new_assign[vm0_2,s1]
   + new_assign[vm0_2,s7] + new_assign[vm0_2,s8] + new_assign[vm0_2,w2]
   + new_assign[vm0_2,w6] + new_assign[vm0_2,w1] <= 1
 requested_vm_single_host[vm1_2]: new_assign[vm1_2,s1]
   + new_assign[vm1_2,s7] + new_assign[vm1_2,s8] + new_assign[vm1_2,w2]
   + new_assign[vm1_2,w6] + new_assign[vm1_2,w1] <= 1
 requested_vm_single_host[vm2_2]: new_assign[vm2_2,s1]
   + new_assign[vm2_2,s7] + new_assign[vm2_2,s8] + new_assign[vm2_2,w2]
   + new_assign[vm2_2,w6] + new_assign[vm2_2,w1] <= 1
 requested_vm_single_host[vm3_2]: new_assign[vm3_2,s1]
   + new_assign[vm3_2,s7] + new_assign[vm3_2,s8] + new_assign[vm3_2,w2]
   + new_assign[vm3_2,w6] + new_assign[vm3_2,w1] <= 1
 requested_vm_single_server[vm1_2]: new_assign[vm1_2,s1]
   + new_assign[vm1_2,s7] + new_assign[vm1_2,s8] = 1
 requested_vm_single_server[vm2_2]: new_assign[vm2_2,s1]
   + new_assign[vm2_2,s7] + new_assign[vm2_2,s8] = 1
 requested_vm_single_server[vm3_2]: new_assign[vm3_2,s1]
   + new_assign[vm3_2,s7] + new_assign[vm3_2,s8] = 1
 req2_dummy_vm: new_assign[vm0_2,w2] = 1
Bounds
Binaries
 new_assign[vm0_2,s1] new_assign[vm0_2,s7] new_assign[vm0_2,s8]
 new_assign[vm0_2,w2] new_assign[vm0_2,w6] new_assign[vm0_2,w1]
 new_assign[vm1_2,s1] new_assign[vm1_2,s7] new_assign[vm1_2,s8]
 new_assign[vm1_2,w2] new_assign[vm1_2,w6] new_assign[vm1_2,w1]
 new_assign[vm2_2,s1] new_assign[vm2_2,s7] new_assign[vm2_2,s8]
 new_assign[vm2_2,w2] new_assign[vm2_2,w6] new_assign[vm2_2,w1]
 new_assign[vm3_2,s1] new_assign[vm3_2,s7] new_assign[vm3_2,s8]
 new_assign[vm3_2,w2] new_assign[vm3_2,w6] new_assign[vm3_2,w1]
 new_assign[(vm0_2,vm1_2),(s1,w1)] new_assign[(vm0_2,vm1_2),(w1,s1)]
 new_assign[(vm0_2,vm1_2),(s1,w6)] new_assign[(vm0_2,vm1_2),(w6,s1)]
 new_assign[(vm0_2,vm1_2),(s7,w1)] new_assign[(vm0_2,vm1_2),(w1,s7)]
 new_assign[(vm0_2,vm1_2),(s8,w2)] new_assign[(vm0_2,vm1_2),(w2,s8)]
 new_assign[(vm0_2,vm1_2),(s8,w6)] new_assign[(vm0_2,vm1_2),(w6,s8)]
 new_assign[(vm1_2,vm2_2),(s1,w1)] new_assign[(vm1_2,vm2_2),(w1,s1)]
 new_assign[(vm1_2,vm2_2),(s1,w6)] new_assign[(vm1_2,vm2_2),(w6,s1)]
 new_assign[(vm1_2,vm2_2),(s7,w1)] new_assign[(vm1_2,vm2_2),(w1,s7)]
 new_assign[(vm1_2,vm2_2),(s8,w2)] new_assign[(vm1_2,vm2_2),(w2,s8)]
 new_assign[(vm1_2,vm2_2),(s8,w6)] new_assign[(vm1_2,vm2_2),(w6,s8)]
 new_assign[(vm2_2,vm3_2),(s1,w1)] new_assign[(vm2_2,vm3_2),(w1,s1)]
 new_assign[(vm2_2,vm3_2),(s1,w6)] new_assign[(vm2_2,vm3_2),(w6,s1)]
 new_assign[(vm2_2,vm3_2),(s7,w1)] new_assign[(vm2_2,vm3_2),(w1,s7)]
 new_assign[(vm2_2,vm3_2),(s8,w2)] new_assign[(vm2_2,vm3_2),(w2,s8)]
 new_assign[(vm2_2,vm3_2),(s8,w6)] new_assign[(vm2_2,vm3_2),(w6,s8)]
End
