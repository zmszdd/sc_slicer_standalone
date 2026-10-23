; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c791a6aab_deposit_open_to_any_caller () Bool)
(declare-fun c791a6aab_lock_expiry_hours () Int)
(declare-fun c791a6aab_min_deposit_wei () Int)
(declare-fun c791a6aab_permanent_dos_holds () Bool)
(declare-fun c791a6aab_victim_ghybr_balance () Int)
(declare-fun c791a6aab_victim_transfer_completes () Bool)
(assert
 (= c791a6aab_deposit_open_to_any_caller c791a6aab_deposit_open_to_any_caller))
(assert
 (= c791a6aab_lock_expiry_hours c791a6aab_lock_expiry_hours))
(assert
 (= c791a6aab_min_deposit_wei c791a6aab_min_deposit_wei))
(assert
 (= c791a6aab_permanent_dos_holds c791a6aab_permanent_dos_holds))
(assert
 (= c791a6aab_victim_ghybr_balance c791a6aab_victim_ghybr_balance))
(assert
 (= c791a6aab_victim_transfer_completes c791a6aab_victim_transfer_completes))
(define-fun report_preconditions () Bool (and c791a6aab_deposit_open_to_any_caller
     (>= 1 c791a6aab_min_deposit_wei)
     (< 0 c791a6aab_victim_ghybr_balance)
     (= 24 c791a6aab_lock_expiry_hours)))
(define-fun report_safety () Bool (=> (and c791a6aab_deposit_open_to_any_caller
         (>= 1 c791a6aab_min_deposit_wei)
         (< 0 c791a6aab_victim_ghybr_balance)
         (= 24 c791a6aab_lock_expiry_hours))
    (and c791a6aab_victim_transfer_completes
         (not c791a6aab_permanent_dos_holds))))
(define-fun report_effects () Bool (and c791a6aab_deposit_open_to_any_caller
     (>= 1 c791a6aab_min_deposit_wei)
     (< 0 c791a6aab_victim_ghybr_balance)
     (= 24 c791a6aab_lock_expiry_hours)
     (not (and c791a6aab_victim_transfer_completes
               (not c791a6aab_permanent_dos_holds)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
