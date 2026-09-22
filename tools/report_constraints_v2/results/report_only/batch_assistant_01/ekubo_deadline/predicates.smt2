; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun execution_time () Int)
(declare-fun user_deadline () Int)
(declare-fun liquidity_operation_completed () Bool)
(assert
 (= execution_time execution_time))
(assert
 (= user_deadline user_deadline))
(assert
 (= liquidity_operation_completed liquidity_operation_completed))
(define-fun report_preconditions () Bool (> execution_time user_deadline))
(define-fun report_safety () Bool (=> (> execution_time user_deadline) (not liquidity_operation_completed)))
(define-fun report_effects () Bool liquidity_operation_completed)
