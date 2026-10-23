; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf565362_balance_ () Int)
(declare-fun cbf565362_balance_reduced_by_defi_mechanism () Bool)
(declare-fun cbf565362_last_underlying_balance () Int)
(declare-fun cbf565362_underflow_revert_occurred () Bool)
(assert
 (= cbf565362_balance_ cbf565362_balance_))
(assert
 (= cbf565362_balance_reduced_by_defi_mechanism cbf565362_balance_reduced_by_defi_mechanism))
(assert
 (= cbf565362_last_underlying_balance cbf565362_last_underlying_balance))
(assert
 (= cbf565362_underflow_revert_occurred cbf565362_underflow_revert_occurred))
(define-fun report_preconditions () Bool (and (< cbf565362_balance_ cbf565362_last_underlying_balance)
     cbf565362_balance_reduced_by_defi_mechanism))
(define-fun report_safety () Bool (=> (and (< cbf565362_balance_ cbf565362_last_underlying_balance)
         cbf565362_balance_reduced_by_defi_mechanism)
    (not cbf565362_underflow_revert_occurred)))
(define-fun report_effects () Bool (and (< cbf565362_balance_ cbf565362_last_underlying_balance)
     cbf565362_balance_reduced_by_defi_mechanism
     (not (not cbf565362_underflow_revert_occurred))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
