; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c831490_attacker_contract_eth_wei () Int)
(declare-fun c4c831490_attacker_frontran () Bool)
(declare-fun c4c831490_selfdestruct_forces_eth () Bool)
(declare-fun c4c831490_swap_and_bridge_completes () Bool)
(declare-fun c4c831490_swap_and_bridge_reverts () Bool)
(declare-fun c4c831490_victim_tx_broadcast () Bool)
(assert
 (= c4c831490_attacker_contract_eth_wei c4c831490_attacker_contract_eth_wei))
(assert
 (= c4c831490_attacker_frontran c4c831490_attacker_frontran))
(assert
 (= c4c831490_selfdestruct_forces_eth c4c831490_selfdestruct_forces_eth))
(assert
 (= c4c831490_swap_and_bridge_completes c4c831490_swap_and_bridge_completes))
(assert
 (= c4c831490_swap_and_bridge_reverts c4c831490_swap_and_bridge_reverts))
(assert
 (= c4c831490_victim_tx_broadcast c4c831490_victim_tx_broadcast))
(define-fun report_preconditions () Bool (and c4c831490_victim_tx_broadcast
     c4c831490_attacker_frontran
     (= 1 c4c831490_attacker_contract_eth_wei)
     c4c831490_selfdestruct_forces_eth))
(define-fun report_safety () Bool (=> c4c831490_victim_tx_broadcast c4c831490_swap_and_bridge_completes))
(define-fun report_effects () Bool (and c4c831490_victim_tx_broadcast
     (not c4c831490_swap_and_bridge_completes)
     c4c831490_swap_and_bridge_reverts
     c4c831490_swap_and_bridge_reverts))
(assert report_preconditions)
(check-sat)
(get-model)
