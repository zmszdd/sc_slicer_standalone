; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun returned_spot_ema () Int)
(declare-fun returned_fast_ema () Int)
(declare-fun returned_slow_ema () Int)
(declare-fun bound_eons_ema () Int)
(declare-fun bound_slow_ema () Int)
(declare-fun bound_fast_ema () Int)
(declare-fun blended_tick_correct () Bool)
(assert
 (= returned_spot_ema returned_spot_ema))
(assert
 (= returned_fast_ema returned_fast_ema))
(assert
 (= returned_slow_ema returned_slow_ema))
(assert
 (= bound_eons_ema bound_eons_ema))
(assert
 (= bound_slow_ema bound_slow_ema))
(assert
 (= bound_fast_ema bound_fast_ema))
(assert
 (= blended_tick_correct blended_tick_correct))
(define-fun report_preconditions () Bool (and (distinct returned_spot_ema returned_fast_ema)
     (= bound_eons_ema returned_spot_ema)
     (= bound_slow_ema returned_fast_ema)
     (= bound_fast_ema returned_slow_ema)))
(define-fun report_safety () Bool (=> (and (= bound_eons_ema returned_spot_ema)
         (= bound_slow_ema returned_fast_ema)
         (= bound_fast_ema returned_slow_ema))
    blended_tick_correct))
(define-fun report_effects () Bool (and (= bound_eons_ema returned_spot_ema)
     (= bound_slow_ema returned_fast_ema)
     (= bound_fast_ema returned_slow_ema)
     (not blended_tick_correct)))
