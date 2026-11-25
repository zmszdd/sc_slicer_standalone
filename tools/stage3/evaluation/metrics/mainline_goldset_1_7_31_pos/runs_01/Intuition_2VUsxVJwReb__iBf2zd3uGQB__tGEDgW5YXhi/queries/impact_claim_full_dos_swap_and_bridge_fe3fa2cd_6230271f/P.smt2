; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0df12d6f_attacker_contract_eth_wei () Int)
(declare-fun c0df12d6f_attacker_frontran_victim () Bool)
(declare-fun c0df12d6f_selfdestruct_forces_eth_to_slipstream () Bool)
(declare-fun c0df12d6f_swap_and_bridge_completes () Bool)
(declare-fun c0df12d6f_swap_and_bridge_reverts () Bool)
(declare-fun c0df12d6f_victim_tx_broadcast () Bool)
(assert
 (= c0df12d6f_attacker_contract_eth_wei c0df12d6f_attacker_contract_eth_wei))
(assert
 (= c0df12d6f_attacker_frontran_victim c0df12d6f_attacker_frontran_victim))
(assert
 (= c0df12d6f_selfdestruct_forces_eth_to_slipstream c0df12d6f_selfdestruct_forces_eth_to_slipstream))
(assert
 (= c0df12d6f_swap_and_bridge_completes c0df12d6f_swap_and_bridge_completes))
(assert
 (= c0df12d6f_swap_and_bridge_reverts c0df12d6f_swap_and_bridge_reverts))
(assert
 (= c0df12d6f_victim_tx_broadcast c0df12d6f_victim_tx_broadcast))
(define-fun report_preconditions () Bool (and c0df12d6f_victim_tx_broadcast
     c0df12d6f_attacker_frontran_victim
     (= 1 c0df12d6f_attacker_contract_eth_wei)
     c0df12d6f_selfdestruct_forces_eth_to_slipstream))
(define-fun report_safety () Bool (=> c0df12d6f_victim_tx_broadcast c0df12d6f_swap_and_bridge_completes))
(define-fun report_effects () Bool (and c0df12d6f_victim_tx_broadcast
     (not c0df12d6f_swap_and_bridge_completes)
     c0df12d6f_swap_and_bridge_reverts))
(assert report_preconditions)
(check-sat)
(get-model)
