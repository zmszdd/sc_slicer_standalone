; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cad9200f0_factory_fee_threshold () Int)
(declare-fun cad9200f0_max_fee_cap () Int)
(declare-fun cad9200f0_swap_fee_value () Int)
(assert
 (= cad9200f0_factory_fee_threshold cad9200f0_factory_fee_threshold))
(assert
 (= cad9200f0_max_fee_cap cad9200f0_max_fee_cap))
(assert
 (= cad9200f0_swap_fee_value cad9200f0_swap_fee_value))
(define-fun report_preconditions () Bool (= 100000 cad9200f0_factory_fee_threshold))
(define-fun report_safety () Bool (=> (> cad9200f0_swap_fee_value cad9200f0_factory_fee_threshold)
    (=> (> cad9200f0_swap_fee_value cad9200f0_factory_fee_threshold)
        (<= cad9200f0_swap_fee_value cad9200f0_max_fee_cap))))
(define-fun report_effects () Bool (and (> cad9200f0_swap_fee_value cad9200f0_factory_fee_threshold)
     (> cad9200f0_swap_fee_value cad9200f0_factory_fee_threshold)
     (not (<= cad9200f0_swap_fee_value cad9200f0_max_fee_cap))))
