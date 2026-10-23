; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbd5c1c04_debt_accounting_executed () Bool)
(declare-fun cbd5c1c04_pool_initialized_at_tick_zero () Bool)
(declare-fun cbd5c1c04_swap_msg_value_eth () Int)
(declare-fun cbd5c1c04_triggered_by_legitimate_swap () Bool)
(declare-fun cbd5c1c04_victim_swap_submitted () Bool)
(assert
 (= cbd5c1c04_debt_accounting_executed cbd5c1c04_debt_accounting_executed))
(assert
 (= cbd5c1c04_pool_initialized_at_tick_zero cbd5c1c04_pool_initialized_at_tick_zero))
(assert
 (= cbd5c1c04_swap_msg_value_eth cbd5c1c04_swap_msg_value_eth))
(assert
 (= cbd5c1c04_triggered_by_legitimate_swap cbd5c1c04_triggered_by_legitimate_swap))
(assert
 (= cbd5c1c04_victim_swap_submitted cbd5c1c04_victim_swap_submitted))
(define-fun report_preconditions () Bool (and cbd5c1c04_pool_initialized_at_tick_zero
     cbd5c1c04_victim_swap_submitted
     (= 10 cbd5c1c04_swap_msg_value_eth)))
(define-fun report_safety () Bool (=> cbd5c1c04_triggered_by_legitimate_swap
    (=> (and cbd5c1c04_victim_swap_submitted (< 0 cbd5c1c04_swap_msg_value_eth))
        cbd5c1c04_debt_accounting_executed)))
(define-fun report_effects () Bool (and cbd5c1c04_triggered_by_legitimate_swap
     cbd5c1c04_victim_swap_submitted
     (< 0 cbd5c1c04_swap_msg_value_eth)
     (not cbd5c1c04_debt_accounting_executed)))
